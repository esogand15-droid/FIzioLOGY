# آناتومی سر و گردن — ساخت جزوه‌ها

> **شروع گفت‌وگوی جدید و وضعیت فعلی:** ابتدا [راهنمای ادامهٔ پروژه](PROJECT_HANDOFF.md) را بخوانید. بخش‌های پایین و دستورهای تاریخی ممکن است قدیمی باشند؛ به‌ویژه `_DRAFT` جلسات ۱ و ۲ با PDFهای فعلی یکسان نیستند و جلسهٔ ۳ اکنون نسخهٔ افزایشی منتشرشده دارد. برای ساخت نسخهٔ فعلی جلسهٔ ۳ باید `HUMSYAR_HN03_WIP=1` تنظیم شود؛ اسکریپت‌های تولید محتوا ممکن است فایل‌های اصلاح‌شده را بازنویسی کنند. از وضعیت و محدودیت‌های ثبت‌شده در راهنما و گزارش QA فعلی استفاده کنید.

## جلسات ۱ و ۲: نسخه‌های موضوعی بازبینی‌شده

خروجی جلسهٔ ۱ در `pdf/HumsYar_HeadNeck_Jalase1.pdf` به قالب موضوعی بازسازی شده است. نام `_DRAFT` جلسهٔ ۱ در حال حاضر کپی همین نسخه برای سازگاری است؛ نسخهٔ صفحه‌محور ردشده جایگزین شده است. این نسخه ۱۷ مبحث، متن تایپ‌شده، ارجاع، شکل و کادر آموزشی دارد و از صفحهٔ کامل جزوه به‌جای متن استفاده نمی‌کند. متن و شکل‌های صفحه‌های منبع و خروجی به‌صورت تصویری مرور شده‌اند؛ مقابلهٔ مستقل نهایی واژه‌به‌واژه هنوز انجام نشده است. این فایل برای کار جزوه‌نویسان تهیه شده، نه به‌عنوان تأیید علمی تخصصی. جزئیات و نقشهٔ قاب‌ها در `headneck/reports/HN_S01_REVIEW_2026.md` است.

خروجی جلسهٔ ۲ در `pdf/HumsYar_HeadNeck_Jalase2.pdf` نسخهٔ موضوعی جایگزین نسخهٔ صفحه‌محور ردشده است. نام `_DRAFT` نیز کپی همین نسخه است. گزارش تصویری، ارجاع‌ها و نگاشت صفحه‌های آن در `headneck/reports/HN_S02_REVIEW_2026.md` آمده است. مقابلهٔ مستقل نهایی واژه‌به‌واژه همچنان انجام نشده است.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# فایل‌های JSON موجود شامل رونویسی اولیه و تصویرهای جای‌گذاری‌شده‌اند.
# برای اعمال دوبارهٔ اصلاحات روی محتوای موجود، ترتیب زیر را رعایت کنید:
.venv/bin/python headneck/scripts/reconcile_hn01_hn02_opening.py
.venv/bin/python headneck/scripts/reconcile_hn01_hn02_middle.py
.venv/bin/python headneck/scripts/reconcile_hn02_later.py
.venv/bin/python headneck/scripts/reconcile_hn02_temporal.py
.venv/bin/python headneck/scripts/reconcile_hn02_review.py
.venv/bin/python headneck/scripts/fix_hn01_figure_crops.py
.venv/bin/python headneck/scripts/refine_hn01_captions.py
.venv/bin/python headneck/scripts/fix_hn02_figure_crops.py
.venv/bin/python headneck/scripts/refine_hn02_captions.py
.venv/bin/python render/build_headneck.py --session hn01 --force
.venv/bin/python render/build_headneck.py --session hn02 --force
.venv/bin/python render/qa_headneck.py --session hn01 --pdf pdf/HumsYar_HeadNeck_Jalase1.pdf --report headneck/reports/HN_S01_QA_REPORT.md
.venv/bin/python render/qa_headneck.py --session hn02 --pdf pdf/HumsYar_HeadNeck_Jalase2.pdf --report headneck/reports/HN_S02_QA_REPORT.md
.venv/bin/python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase1.pdf pdf/HumsYar_HeadNeck_Jalase2.pdf
```

سازندهٔ صفحه‌محور قدیمی `headneck/scripts/build_hn_verbatim.py` و گزارش `HN_S01_S02_VERBATIM_REVIEW.md` فقط برای ردیابی نسخهٔ ردشده نگهداری شده‌اند و در ساخت پیش‌نویس استفاده نمی‌شوند. ابزار QA صرفاً کنترل فنی است و وفاداری متن یا تناسب تصویر را اثبات نمی‌کند.

## جلسهٔ ۳: الگوی چیدمان

خروجی `pdf/HumsYar_HeadNeck_Jalase3.pdf` همان نسخهٔ موجود و الگوی چیدمان برای جلسات ۱ و ۲ است و در این مرحله تغییر نکرده است. گزارش منابع: `headneck/reports/HN_S03_SOURCE_REVIEW.md`؛ گزارش تصویرها: `headneck/reports/HN_S03_IMAGE_AUDIT.md`.

```sh
.venv/bin/python headneck/scripts/hn03_figures.py
.venv/bin/python headneck/scripts/hn03_build_content.py
.venv/bin/python headneck/scripts/audit_hn03_illustrations.py
.venv/bin/python render/build_headneck.py --session hn03 --force
.venv/bin/python render/qa_headneck.py --session hn03
.venv/bin/python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase3.pdf
```

PDFهای خروجی در `.gitattributes` باینری مشخص شده‌اند تا فایل و فونت‌ها در انتقال دچار تبدیل متن نشوند.
