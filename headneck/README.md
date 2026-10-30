# آناتومی سر و گردن — ساخت جزوه‌ها

## جلسات ۱ و ۲: صفحات اصلی بدون بازنویسی

خروجی‌های `pdf/HumsYar_HeadNeck_Jalase1.pdf` و `pdf/HumsYar_HeadNeck_Jalase2.pdf` صفحات کامل جزوه‌های اصلی را بدون بازنویسی و به‌ترتیب حفظ می‌کنند. قاب‌های منتخب نتر و گری صفحه‌های تکمیلی مستقل‌اند و پس از صفحهٔ مرتبط جزوه آمده‌اند. به همین دلیل، ظاهر متن اصلی خودِ صفحهٔ جزوه است و مانند نسخهٔ قدیمی حروف‌چینی مجدد نشده است. فایل‌های JSON قدیمی `hn01_*` و `hn02_*` هنوز در مخزن برای تاریخچه و مطالعهٔ نسخهٔ قبلی هستند ولی متن این دو PDF جدید از آن‌ها تولید نمی‌شود.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python render/build_headneck.py --session hn01 --force
.venv/bin/python render/build_headneck.py --session hn02 --force
.venv/bin/python render/qa_headneck.py --session hn01
.venv/bin/python render/qa_headneck.py --session hn02
.venv/bin/python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase1.pdf pdf/HumsYar_HeadNeck_Jalase2.pdf
```

سازندهٔ این دو جلسه `headneck/scripts/build_hn_verbatim.py` و فهرست جای تصاویر `headneck/content/hn_verbatim_figures.json` است. ابزار QA جدید جریان محتوای هر صفحهٔ منبع را با خروجی مقایسه می‌کند، رندر هر صفحه را با تحمل گردکردن حداکثر ۲ واحد رنگ می‌سنجد و محتوای تصویرهای مرجع و جای آن‌ها را کنترل می‌کند. تفاوت ترتیب استخراج متنی در بعضی صفحه‌های فارسی/انگلیسی همچنان ممکن است. نگاشت صفحات و محدودیت‌های بررسی در `headneck/reports/HN_S01_S02_VERBATIM_REVIEW.md` و فایل‌های `HN_S01_VERBATIM_MAP.json` و `HN_S02_VERBATIM_MAP.json` است. این کنترل‌ها جایگزین داوری تخصصی علمی نیستند و بررسی کل تصاویر کتاب‌های مرجع ادعا نشده است.

## جلسهٔ ۳: نسخهٔ بازنویسی‌شدهٔ قبلی

خروجی `pdf/HumsYar_HeadNeck_Jalase3.pdf` همچنان از JSON تولید می‌شود و متن آن بازنویسی شده است؛ با شرط جدید حفظ لفظی متن منبع منطبق نیست. گزارش منابع: `headneck/reports/HN_S03_SOURCE_REVIEW.md`؛ گزارش تصویرها: `headneck/reports/HN_S03_IMAGE_AUDIT.md`.

```sh
.venv/bin/python headneck/scripts/hn03_figures.py
.venv/bin/python headneck/scripts/hn03_build_content.py
.venv/bin/python headneck/scripts/audit_hn03_illustrations.py
.venv/bin/python render/build_headneck.py --session hn03 --force
.venv/bin/python render/qa_headneck.py --session hn03
.venv/bin/python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase3.pdf
```

PDFهای خروجی در `.gitattributes` باینری مشخص شده‌اند تا فایل و فونت‌ها در انتقال دچار تبدیل متن نشوند.
