# دليل النشر — PrintShop Local

## مخطط الشبكة

```
                    ┌──────────────────┐
                    │   موجه WiFi      │
                    │  LAIDANI_PRINT   │
                    │  192.168.1.1     │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────┴─────┐    ┌──────┴──────┐    ┌─────┴─────┐
    │  PC1      │    │  PC2       │    │  PC3      │
    │  192.168. │    │  192.168.  │    │  192.168. │
    │  1.101    │    │  1.102     │    │  1.103    │
    │  Station 1│    │  Station 2 │    │  Station 3│
    └───────────┘    └────────────┘    └───────────┘
```

## إعدادات IP

| الجهاز | IP | الدور |
|--------|----|-------|
| المودم | 192.168.1.1 | موجه WiFi + Captive Portal |
| PC1 | 192.168.1.101 | Station 1 |
| PC2 | 192.168.1.102 | Station 2 |
| PC3 | 192.168.1.103 | Station 3 |
| PC4 | 192.168.1.104 | Station 4 |

## التشغيل التلقائي مع Windows

استخدم **Task Scheduler** لتشغيل `start.bat` تلقائياً عند بدء التشغيل:

1. افتح Task Scheduler
2. Create Basic Task
3. Trigger: When the computer starts
4. Action: Start a program
5. Program: `start.bat`
6. Finish

## استراتيجية النسخ الاحتياطي

### قاعدة البيانات
- الموقع: `db/printshop.db`
- انسخها يومياً إلى مجلد آخر أو سحابة

### الملفات المرفوعة
- الموقع: `uploads/`
- تحذف تلقائياً بعد 7 أيام (قابلة للتعديل)

### النسخ الاحتياطي الكامل
```batch
copy db\printshop.db backups\%date:~-10,4%%date:~-7,2%%date:~-4,2%_printshop.db
```

## التطوير المستقبلي

### Supabase (جاهز، غير مفعل)
عدّل في `config.py`:
```python
SUPABASE_ENABLED = True
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
```
ثم شغّل `supabase_schema.sql` في Supabase SQL Editor.

### تطبيق Flutter (المرحلة 3)
التطبيق المستقبلي سيسمح للزبون بـ:
- متابعة حالة الطلب
- إشعار عند الجهوزية
- تقييم الخدمة
