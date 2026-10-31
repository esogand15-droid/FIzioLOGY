# جزوهٔ مادر سر و گردن — جلسهٔ چهارم

## وضعیت این شاخه

شاخهٔ `arena/3260a120-fiziology` از نسخهٔ اولیهٔ مخزن ساخته شده بود و محتوای جزوهٔ مادر را نداشت. برای ادامهٔ راهنمای پیوست، **فقط وابستگی‌های جلسهٔ ۴** از commit `026cbcc1191751a491bcb37675adcb2cb8c827d0` بازیابی شد؛ شاخه عوض یا merge نشد. نبود فایل‌های جلسات دیگر در این شاخه به معنی حذف نسخه‌های آن‌ها از تاریخچه نیست.

- `pdf/HumsYar_HeadNeck_Jalase4.pdf`: نسخهٔ قبلی ۹۰ صفحه، بازیابی بایتی؛ جایگزین نشده است.
- `pdf/HumsYar_HeadNeck_Jalase4_REVIEW.pdf`: نسخهٔ افزایشی جدید، **۱۰۵ صفحه و در انتظار بازبینی نهایی**.
- [گزارش تغییرات و محدودیت‌ها](reports/HN_S04_UPDATE_2026.md)
- [گزارش فنی نسخهٔ جدید](reports/HN_S04_UPDATE_QA_REPORT.md)
- [tracker](reports/HN_S04_QA_TRACKER.md)
- [شواهد ماشینی](reports/hn04_audit_evidence/manifest.json)
- [شواهد بازبینی دستی محدود به SHA مشخص](reports/hn04_audit_evidence/manual_review.json)

`INDEX.json` فهرست تاریخی کامل بازیابی‌شده است، ولی فقط تصاویر مصرفی جلسهٔ چهارم در این شاخه بازیابی شده‌اند؛ وجود ردیف مربوط به جلسه‌ای دیگر به معنی آماده‌بودن دارایی‌ها یا PDF آن جلسه نیست.

## ساخت و آزمون

از ریشهٔ مخزن:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s headneck/tests -v
.venv/bin/python render/build_headneck.py --session hn04 --out .cache/hn04_candidate.pdf
.venv/bin/python render/qa_headneck.py --session hn04 --pdf .cache/hn04_candidate.pdf --report .cache/hn04_qa.md
.venv/bin/python headneck/scripts/verify_pdf_integrity.py .cache/hn04_candidate.pdf
.venv/bin/python headneck/scripts/audit_hn04_update.py --pdf .cache/hn04_candidate.pdf --out .cache/hn04_evidence.json
```

مسیر پیش‌فرض سازنده و QA برای hn04 عمداً فایل `_REVIEW` و گزارش `HN_S04_UPDATE_QA_REPORT.md` است تا نسخه و گزارش قدیمی بازنویسی نشوند. `--force` فقط برای بازسازی همان فایل است. metadata می‌تواند SHA نامزد تازه را تغییر دهد؛ شواهد تصویری SHA قبلی را تأیید فایل تازه ندانید.

## محتوا و تصویر

- `hn04_a.json` و `hn04_b.json` محتوای پایهٔ بازیابی‌شده‌اند؛ رونویسی تغییر نکرده است.
- `hn04_update.json` لایهٔ افزایشی ۲۰ مبحث است؛ متن اصلی و افزوده‌ها تفکیک شده‌اند.
- ساخت مجدد لایه: `headneck/scripts/prepare_hn04_update.py`؛ فقط فایل update را می‌نویسد.
- چهار قاب تازه: `headneck/scripts/hn04_reference_assets.py`؛ فقط دارایی‌های نام‌دار جدید و ردیف‌های همان دارایی‌ها در INDEX را می‌نویسد. اجرای آن، منابع اصلی PDF را تغییر نمی‌دهد.
- `hn04_overlay_figures.py` درج قاب‌های تازه و metadata نمایش قاب‌های قبلی را مشخص می‌کند.
- آزمون حفظ ۵۸۶ بلوک پایه، درستی مستقل رونویسی آن‌ها نسبت به PDF منبع را اثبات نمی‌کند.
- کنترل محدودهٔ متن و تطابق بایتی تصاویر PDF، صحت علمی یا خوانده‌شدن تمامی ریزبرچسب‌ها را اثبات نمی‌کند.

بازسازی اسکریپت‌های تاریخی `prepare_hn04_content.py` به این شاخه منتقل نشده است تا اشتباهاً JSON پایه و INDEX را بازنویسی نکند. برای تاریخچهٔ کامل به commit بازیابی مراجعه کنید.
