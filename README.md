# dorar-feqhia

استخراج الموسوعة الفقهية من [dorar.net/feqhia](https://dorar.net/feqhia) بأكواد Python.

## هيكل المشروع

```
dorar-feqhia/
├── scraper/
│   ├── explore.py   # بناء فهرس المحتوى (TOC)
│   ├── fetch.py     # جلب محتوى الصفحات (قريباً)
│   └── export.py    # تصدير JSON / CSV (قريباً)
└── data/
    ├── toc.json     # فهرس المحتوى المستخرج
    └── pages/       # ملفات الصفحات
```

## تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

## الاستخدام

### 1. بناء فهرس المحتوى

```bash
python -m scraper.explore
```

يولّد `data/toc.json` بالهيكل الكامل:
`كتاب → باب → فصل → مبحث → مطلب → فرع`

## ملاحظة

يُرجى الالتزام بالاستخدام البحثي والأكاديمي واحترام حقوق الموقع.
