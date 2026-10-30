# آناتومی سر و گردن — ساخت جلسهٔ ۳

خروجی: `pdf/HumsYar_HeadNeck_Jalase3.pdf`. گزارش منابع و محدودیت‌ها: `headneck/reports/HN_S03_SOURCE_REVIEW.md`؛ گزارش خودکار: `headneck/reports/HN_S03_QA_REPORT.md`؛ نگاشت تصویر به تصویر و دامنهٔ بررسی: `headneck/reports/HN_S03_IMAGE_AUDIT.md`.

از ریشهٔ مخزن، با Python و فایل‌های منبع موجود در مخزن:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python headneck/scripts/hn03_figures.py
.venv/bin/python headneck/scripts/hn03_build_content.py
.venv/bin/python headneck/scripts/audit_hn03_illustrations.py
.venv/bin/python render/build_headneck.py --session hn03 --force
.venv/bin/python render/qa_headneck.py --session hn03
```

شمارهٔ صفحه‌های منبع در JSON شمارهٔ یک‌مبنای فایل PDF است، نه شمارهٔ چاپی پایین جزوه. فایل‌های `hn03_a.json` و `hn03_b.json` از اسکریپت محتوا تولید می‌شوند؛ برای حفظ ویرایش‌ها اسکریپت را تغییر دهید و دوباره اجرا کنید. تصاویر از PDFهای منبع بازتولید می‌شوند و مشخصات آن‌ها در `headneck/images/INDEX.json` ثبت است. ساخت جلسات ۱ و ۲ نیازمند محتوا و تصاویر همان جلسه است؛ PDFهای بازیابی‌شدهٔ آن‌ها در `pdf/` دست‌نخورده‌اند.

برای کنترل سلامت فایل پس از ساخت یا انتقال (xref و فونت‌های جاسازی‌شده):

```sh
.venv/bin/python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase3.pdf
```

PDFهای پوشهٔ `pdf/` در `.gitattributes` باینری مشخص شده‌اند. خطای مخدوش‌شدن داده‌های باینری می‌تواند فونت را در نمایشگر مرورگر خراب کند، حتی اگر بعضی ابزارها فایل را در حالت بازیابی باز کنند.

گزارش ممیزی جاری و موارد باقی‌ماندهٔ جلسات موجود: `headneck/reports/HN_CROSS_SESSION_AUDIT.md`. این گزارش صراحتاً وضعیت ناتمام تطبیق متن و تصاویر را ثبت می‌کند.
