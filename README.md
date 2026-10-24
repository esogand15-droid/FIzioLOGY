# HumsYar — جزوه مادر جامع فیزیولوژی اعصاب و حواس ویژه

این مخزن، خروجی پروژه «تجمیع و تطبیق منابع درس فیزیولوژی اعصاب و حواس ویژه» برای تیم
جزوه‌نویسی است. خروجی اصلی:

```
output/HumsYar_Neuro_SpecialSenses_Master.pdf   (۶۰۰+ صفحه)
```

## زنجیره پردازش (قابل اجرا و قابل بازتولید)

| مرحله | اسکریپت | خروجی |
|---|---|---|
| ۱ | `scripts/01_fetch_sources.py` | `work/source_download_manifest.csv`, `src/extracted/` |
| ۲ | `scripts/02_extract.py` | `work/source_registry.json`, `work/page_data/`, `work/extracted_text/` |
| ۳ | `scripts/03_figures.py` | `images/extracted/`, `images/INDEX.json` |
| ۴ | `scripts/04_sections.py` | `work/sections.json` |
| ۵ | `scripts/05_reflow.py` | `work/flows/` (پاراگراف‌بندی و شماره صفحه) |
| ۶ | `scripts/06_normalize.py` | `work/flows_norm/`, `work/normalization_log.json` |
| ۷ | `scripts/07_align_pages.py` | `work/pages_map.json` (تطبیق MD↔PDF) |
| ۸ | `scripts/08_build_content.py` | `lock/chapters/*.json`, `lock/manifest.json` |
| ۹ | `scripts/09_appendix_pages.py` | `images/appendix/` (تصویر صفحه جزوه‌های مخدوش) |
| ۹b | `scripts/09b_guyton_index.py` | `work/guyton_index.json` (نمایه گایتون) |
| ۱۰ | `render/render.py` | `output/*.pdf`, `lock/section_pages.json` |
| ۱۱ | `scripts/10_reports.py` | `inventory/*`, `reports/*`, `lock/figures/` |

اجرا:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/01_fetch_sources.py
for s in 02_extract 03_figures 04_sections 05_reflow 06_normalize 07_align_pages \
         08_build_content 09_appendix_pages ; do .venv/bin/python scripts/$s.py ; done
.venv/bin/python render/render.py
.venv/bin/python scripts/10_reports.py
```

## قواعد محتوایی رعایت‌شده

- متن منابع بازنویسی آزاد نشده؛ تنها شکست سطرها، فاصله‌ها و خطاهای قطعی و فهرست‌شده
  (در `work/normalization_log.json`) اصلاح شده‌اند.
- هر بلوک متن/شکل، شناسه منبع (`SRC-xxxx`) و شماره صفحه دارد.
- متن‌های مخدوش (جزوه‌های ۱۴۰۲) اصلاح حدسی نشده‌اند؛ تصویر صفحه‌های آن‌ها در «پیوست تصویری»
  آمده است.
- تفاوت‌های عددی میان منابع، در کارت «⚠ اختلاف منابع» ثبت شده و هیچ‌کدام خودسرانه ترجیح
  داده نشده است.
- مطالب کلاس‌های دکتر قدیری/ایروان‌پور و جزوه‌های ۱۴۰۲ به‌عنوان «تکمیل» و با ذکر منبع
  جدا شده‌اند.

## محدودیت‌های شناخته‌شده

1. ویدئوهای جلسات در مخزن به‌صورت Git LFS هستند و در این اجرا دانلود نشدند
   (۳۲ فایل) ⇒ ترنسکریپت و فریم ویدئویی وجود ندارد.
2. سه فایل گایتون (نسخه انگلیسی و دو جلد فارسی) LFS هستند و دریافت نشدند ⇒ تطبیق
   صفحه‌به‌صفحه انجام نشده است.
3. متن جزوه‌های ۱۴۰۲ نیازمند OCR فارسی است.
4. مبحث چشایی/بویایی در منابع، جلسه اختصاصی ندارد.
5. پاورپوینت (pptx) در مخزن موجود نیست.

جزئیات در `reports/CONTENT_AUDIT.md`، `reports/FIGURE_AUDIT.md`، `reports/FINAL_QC.md`،
`inventory/INVENTORY.md`، `inventory/SOURCE_MAP.csv` و `inventory/SOURCE_COVERAGE.md`.
