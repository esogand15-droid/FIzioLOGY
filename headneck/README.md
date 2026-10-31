# جزوهٔ مادر سر و گردن — جلسهٔ چهارم

## نسخهٔ جاری: FINAL

- [دانلود PDF نهایی ۱۲۲صفحه‌ای](../pdf/HumsYar_HeadNeck_Jalase4_FINAL.pdf)
- [گزارش بازبینی نهایی، اصلاح‌ها و محدودیت‌ها](reports/HN_S04_FINAL_REVIEW_REPORT.md)
- [ماتریس صفحه/شکل/زیرشکل منبع و مرجع](reports/HN_S04_FINAL_SOURCE_SUBFIGURE_MATRIX.md)
- [گزارش QA فنی](reports/HN_S04_FINAL_TECHNICAL_QA_REPORT.md)
- [وضعیت بازبینی](reports/HN_S04_QA_TRACKER.md) و [راهنمای ادامه](PROJECT_HANDOFF.md)

SHA-256 PDF: `85e6c0b234f14592d399f234039138d15eee870fdc2e4f22cece234c7e72714b`

۲۰ مبحث، ۶۹۹ بلوک، ۶۹ قاب تصویر؛ همهٔ ۳۹ صفحهٔ منبع و ۱۲۲ صفحهٔ خروجی دیده شدند. مرور متن و زیرشکل‌ها از کنترل ماشینی جدا ثبت شده است. ۱۵ هشدار کم‌بودن برچسب خلاصه، همگی تعیین تکلیف شده‌اند؛ صفر خطای سخت. وضوح/واترمارک اصل و بعضی آثار کوچک حاشیه باقی است؛ نمای کلی نتر ۳۲ برای ریزبرچسب‌ها نیازمند زوم است. این نسخهٔ نهایی **ویرایشی/آموزشی** است، نه تأیید مستقل متخصص بالینی.

دامنهٔ مرجع: نتر PDF ۸۱–۸۶، ۱۱۳–۱۱۵ و ۱۷۷؛ گری (قطعهٔ ۸۰۱–۱۰۰۰) PDF ۸۸–۹۷. ادعای جست‌وجوی تمام صفحات دو کتاب نداریم؛ موجودی مستقل علت انتخاب/عدم درج نماهای همراه را می‌گوید.

### شواهد

داخل [`reports/hn04_final_evidence/`](reports/hn04_final_evidence/):
- `manual_review.json` و `pages/`: ثبت مشاهدهٔ ۱۲۲ صفحه با SHA همین PDF و hash هر تصویر.
- `source_editorial_review.json`، `source_text_pairs.json` و `sources/`: مقابلهٔ ۳۹ صفحهٔ دو بخش، شکل‌ها/زیرشکل‌ها و سه اصلاح تیتر.
- `reference_editorial_inventory.json` و `atlas/`: ۲۰ صفحهٔ مرجع و تصمیم هر نما.
- `machine_manifest.json`: نگاشت بایتی دارایی‌ها/صفحه‌های خروجی؛ وضعیت‌های دستی این فایل عمداً خودکار تأیید نمی‌شوند.
- `layout_trace.json`: رد بلوک‌ها؛ `page_before` لزوماً صفحهٔ واقعی شروع بلوک نیست.

## ساخت و آزمون

از ریشهٔ مخزن:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s headneck/tests -v
.venv/bin/python headneck/scripts/verify_hn04_final_evidence.py
# برای ساخت نامزد جدا، بدون بازنویسی FINAL منتشرشده:
.venv/bin/python render/build_headneck.py --session hn04 --out .cache/hn04_candidate.pdf
.venv/bin/python render/qa_headneck.py --session hn04 --pdf .cache/hn04_candidate.pdf --report .cache/hn04_qa.md
.venv/bin/python headneck/scripts/verify_pdf_integrity.py .cache/hn04_candidate.pdf
.venv/bin/python headneck/scripts/audit_hn04_update.py --pdf .cache/hn04_candidate.pdf --out .cache/hn04_evidence.json
```

۱۵ آزمون integration/evidence وجود دارد. آزمون hash/پوشش فقط پیوستگی شواهد را می‌سنجد، نه اینکه یک ماشین «صفحه را خوانده» یا واژه‌ای را از نظر علمی تأیید کرده باشد.

پیش‌فرض builder و QA برای hn04 اکنون `_FINAL.pdf` و `HN_S04_FINAL_TECHNICAL_QA_REPORT.md` است؛ فایل موجود بدون `--force` بازنویسی نمی‌شود. ساخت می‌تواند metadata/hash تازه ایجاد کند. شواهد تصویری و ثبت مشاهدهٔ نسخهٔ قبلی را به فایل تازه منتقل نکنید؛ بعد از تغییر PDF بازبینیِ SHA جدید لازم است.

## محتوا و دارایی

- `hn04_a.json` و `hn04_b.json`: پایهٔ ثابت؛ ۵۸۶ بلوک پایه محفوظ‌اند. سه نقص لفظی تیتر در overlay به‌صورت صریح و با `expected_text` اصلاح می‌شوند.
- `hn04_update.json`: لایهٔ افزایشی ۲۰ مبحث؛ نقل اصل، جدول/کادر آموزشی و رفع ابهام از هم جدا هستند.
- `prepare_hn04_update.py`: سازندهٔ update؛ شامل `hn04_final_review.py` برای اصلاح‌ها/افزوده‌های دور نهایی.
- `hn04_reference_assets.py`: چهار قاب مرجعِ دور REVIEW؛ `hn04_final_assets.py`: هجده برش دور FINAL با bbox و پنج ماسک مستند.
- `hn04_overlay_figures.py`: درج قاب‌های دور قبلی و metadata نمایش؛ اندازه/صفحه‌شکنی‌های نهایی در `hn04_final_review.py` است.
- INDEX تاریخیِ جلسات دیگر هم ردیف دارد؛ وجود ردیف به معنی حضور آن دارایی در checkout نیست. همهٔ دارایی‌های مصرفی جلسهٔ ۴ و مسیر منبع آن‌ها کنترل شده‌اند.

اسکریپت‌های تاریخیِ بازسازی پایه را بدون بررسی اجرا نکنید؛ می‌توانند JSON پایه و INDEX را بازنویسی کنند. برای اصلاح جدید ابتدا نامزد مستقل بسازید.

## سوابق محفوظ

- `pdf/HumsYar_HeadNeck_Jalase4.pdf`: پایهٔ ۹۰صفحه‌ای، SHA `0ff3d00c6537a7cf7996924ee9759e1aee8773c8a50a7b44fd9b29c587936772`.
- `pdf/HumsYar_HeadNeck_Jalase4_REVIEW.pdf`: نامزد تاریخی ۱۰۵صفحه‌ای، منتشرشده در `08bfbcc`؛ SHA `84c261bdcb88acb0835cfba0b70ec46bc674a5c95ce5a49cb72c9fe750846eb1`.
- `HN_S04_UPDATE_2026.md`، `HN_S04_UPDATE_QA_REPORT.md` و `hn04_audit_evidence/`: فقط گزارش/شواهد همان REVIEW؛ وضعیت جاری FINAL را توصیف نمی‌کنند.
- شاخهٔ ثابت این جلسه: `arena/3260a120-fiziology`. وابستگی‌های جلسهٔ ۴ ابتدا از `026cbcc` بازیابی شدند؛ وضعیت سایر جلسات در handoff تاریخی است و باید با فایل واقعی دوباره بررسی شود.
