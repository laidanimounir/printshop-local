```
  _      ____       _       _   _   _      ___   _   _   _____
 | |    |  _ \     (_)     | \ | | | |    |_ _| | \ | | | ____|
 | |    | |_) |     _      |  \| | | |     | |  |  \| | |  _|
 | |___ |  __/     | |     | |\  | | |___  | |  | |\  | | |___
 |_____||_|        |_|     |_| \_| |_____||___| |_| \_| |_____|

  🖨️ نظام استقبال طلبات الطباعة — LAIDANI PHONE 🇩🇿
```

[![Python](https://img.shields.io/badge/Python-3.8%2B-6B3F1F?style=flat&logo=python&logoColor=F5C518)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-8B5E3C?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-F5C518?style=flat)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-2ECC71?style=flat)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-3498DB?style=flat&logo=windows&logoColor=white)]()

---

**PrintShop Local** هو نظام محلي (بدون إنترنت) لأتمتة محلات الطباعة. الزبون يمسح QR Code قدام أي كمبيوتر في المحل، يرفع ملفه، ويستلم رقم طلب — بدون واتساب، بدون تطبيق، بدون إنترنت.

> **🇫🇷** Système local de gestion des impressions. Le client scanne un QR Code, télécharge son fichier, et reçoit un numéro de commande — sans WhatsApp, sans application, sans Internet.

---

## ✨ المميزات

| الميزة | الوصف |
|--------|-------|
| 📱 **Captive Portal** | اتصال تلقائي بشبكة WiFi + فتح الصفحة تلقائياً |
| 🖨️ **طباعة مباشرة** | طباعة بضغطة زر عبر win32print |
| 🔔 **إشعارات صوتية** | صوت عند وصول طلب جديد |
| 🔄 **تحويل الطلبات** | تحويل بين المحطات عند عطل الطابعة |
| 📊 **تقارير وإحصائيات** | رسوم بيانية، إيرادات، ساعات الذروة |
| 👥 **إدارة العمال** | 4 عمال + مدير، صلاحيات مختلفة |
| 📦 **PWA** | تثبيت كتطبيق على هاتف الزبون |
| 🌐 **Supabase** | جاهز للمزامنة السحابية (غير مفعل افتراضياً) |
| ⚙️ **إعدادات متغيرة** | أسعار، أسماء، كل شيء قابل للتعديل |

## 🗺️ بنية الشبكة

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
    │  👨‍🔧 w1   │    │  👨‍🔧 w2    │    │  👨‍🔧 w3   │
    └───────────┘    └────────────┘    └───────────┘
```

## 🚀 تركيب سريع

```bash
# 1. شغل setup.bat كمسؤول
setup.bat

# 2. شغل السيرفر
start.bat
```

أو يدوياً:
```bash
pip install -r requirements.txt
python server.py
```

## 🔑 الحسابات الافتراضية

| المستخدم | كلمة السر | الدور |
|----------|-----------|-------|
| `admin` | `admin123` | مدير 👑 |
| `worker1` | `pass1` | Station 1 |
| `worker2` | `pass2` | Station 2 |
| `worker3` | `pass3` | Station 3 |
| `worker4` | `pass4` | Station 4 |

## 📂 هيكل المشروع

```
printshop-local/
├── app.py              ← إنشاء تطبيق Flask
├── server.py           ← جميع المسارات (Routes)
├── config.py           ← الإعدادات
├── database.py         ← قاعدة البيانات (SQLite + SQLAlchemy)
├── auth.py             ← التوثيق (Flask-Login)
├── printer.py          ← الطباعة (win32print)
├── qr_generator.py     ← توليد QR Code
├── generate_logo.py    ← توليد الشعار
├── file_handler.py     ← معالجة الملفات المرفوعة
├── receipt_generator.py ← طباعة وصل الاستلام
├── security.py         ← الأمان والتحقق
├── logger.py           ← تسجيل الأحداث
├── captive_portal.py   ← نظام Captive Portal
├── supabase_sync.py    ← مزامنة سحابية (Supabase)
├── seed_data.py        ← بيانات تجريبية
├── test_system.py      ← اختبارات آلية
├── templates/          ← قوالب HTML
│   ├── client.html     ← صفحة الزبون
│   ├── confirm.html    ← صفحة التأكيد
│   ├── worker_login.html
│   ├── worker_dashboard.html
│   ├── manager_dashboard.html
│   ├── manager_workers.html
│   ├── manager_reports.html
│   ├── manager_settings.html
│   ├── 404.html / 500.html / 413.html
├── static/
│   ├── css/main.css    ← التصميم الكامل
│   ├── js/main.js      ← JavaScript العام
│   ├── js/worker.js    ← JavaScript العامل
│   ├── manifest.json   ← PWA manifest
│   └── sw.js           ← Service Worker
├── uploads/            ← الملفات المرفوعة
├── qrcodes/            ← أكواد QR المولدة
└── db/                 ← قاعدة البيانات
```

## 🛠️ التقنيات

| التقنية | الاستخدام |
|---------|-----------|
| Python 3.14 | لغة البرمجة |
| Flask | إطار العمل |
| SQLAlchemy + SQLite | قاعدة البيانات |
| Flask-Login | التوثيق |
| win32print | الطباعة على Windows |
| Pillow | معالجة الصور |
| qrcode | توليد QR Code |
| ReportLab | توليد PDF |
| Chart.js | الرسوم البيانية |
| PWA | تطبيق ويب قابل للتثبيت |

## 📡 API Reference

### Public
- `GET /upload/<computer_id>` — صفحة رفع الملفات
- `POST /submit/<computer_id>` — رفع ملف + إنشاء طلب
- `GET /confirm/<order_number>` — صفحة التأكيد

### Worker
- `GET /worker/dashboard` — لوحة العامل
- `POST /worker/print/<id>` — طباعة
- `POST /worker/done/<id>` — تأكيد الإنجاز
- `POST /worker/transfer/<id>` — تحويل الطلب

### Manager
- `GET /manager/dashboard` — لوحة المدير
- `GET /manager/workers` — إدارة العمال
- `GET /manager/reports` — التقارير
- `GET /manager/reports/export` — تصدير PDF
- `GET/POST /manager/settings` — الإعدادات

### API JSON
- `GET /api/orders/<computer_id>` — قائمة الطلبات
- `GET /api/orders/new/<computer_id>?since=N` — الطلبات الجديدة (polling)
- `GET /api/stats/today` — إحصائيات اليوم

## 🗺️ Roadmap

### ✅ الإصدار 1.0 (حالي)
- النظام الأساسي كامل مع 4 محطات
- QR Code لكل محطة
- لوحة تحكم العامل والمدير
- التقارير والإحصائيات
- نظام تحويل الطلبات

### 🔄 الإصدار 2.0 (قريباً)
- مزامنة Supabase
- نسخ احتياطي تلقائي
- إشعارات SMS للزبون

### 📱 الإصدار 3.0 (مستقبل)
- تطبيق Flutter للزبون
- إشعار "ملفك جاهز"
- متابعة حالة الطلب

## 🤝 المساهمة

المشروع مفتوح المصدر. رحّب بالمساهمات!

## 📄 التراخيص

MIT License — حر في الاستخدام والتعديل والتوزيع.

---

<p align="center">🖨️ <strong>LAIDANI PHONE</strong> — طباعة سريعة واحترافية 🇩🇿</p>
