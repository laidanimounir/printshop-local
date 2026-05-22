-- Run this SQL in your Supabase SQL Editor to create the tables

CREATE TABLE IF NOT EXISTS public.orders (
  id BIGSERIAL PRIMARY KEY,
  order_number TEXT UNIQUE NOT NULL,
  computer_id TEXT NOT NULL,
  worker_id BIGINT,
  customer_phone TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT,
  copies INTEGER DEFAULT 1,
  color_mode TEXT DEFAULT 'bw',
  paper_size TEXT DEFAULT 'A4',
  notes TEXT,
  status TEXT DEFAULT 'new',
  price REAL DEFAULT 0,
  page_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.workers (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  computer_id TEXT,
  role TEXT DEFAULT 'worker',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.worker_stats (
  id BIGSERIAL PRIMARY KEY,
  worker_id BIGINT REFERENCES public.workers(id),
  date DATE NOT NULL,
  orders_count INTEGER DEFAULT 0,
  pages_count INTEGER DEFAULT 0,
  revenue REAL DEFAULT 0,
  UNIQUE(worker_id, date)
);

CREATE TABLE IF NOT EXISTS public.settings (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value TEXT
);

-- Enable Row Level Security
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.worker_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

-- Policies: only authenticated users can read/write
CREATE POLICY "Authenticated can read orders"
  ON public.orders FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Authenticated can insert orders"
  ON public.orders FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated can update orders"
  ON public.orders FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated can read workers"
  ON public.workers FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated can read worker_stats"
  ON public.worker_stats FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Authenticated can insert worker_stats"
  ON public.worker_stats FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated can read settings"
  ON public.settings FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Authenticated can update settings"
  ON public.settings FOR UPDATE USING (auth.role() = 'authenticated');

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.orders;
ALTER PUBLICATION supabase_realtime ADD TABLE public.worker_stats;
