"""WIP: transcribe the opening lecture pages into the existing mother-note layout.

Run on the current topic JSONs after applying the figure-placement scripts. This
is deliberately limited to session 1 pages 3–5 and session 2 pages 3–5; the
remaining paragraphs are the older paraphrases and must not be represented as
a complete verbatim transcription. Existing image blocks are retained.
"""
from __future__ import annotations

import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / "content"


def lecture(text: str, page: int) -> dict:
    return {"type": "p", "text": text, "src": f"متن جزوهٔ درس، ص {page} — رونویسی در حال مقابله"}


def heading(text: str) -> dict:
    return {"type": "h3", "text": text}


def image(topic: dict, name: str) -> dict:
    return next(b for b in topic["blocks"] if b.get("asset", "").endswith(name + ".jpeg"))


def indexed(topics: list[dict]) -> dict[str, dict]:
    return {t["topic_id"]: t for t in topics}


def wrap(topic: dict, blocks: list[dict]) -> None:
    # Keep the original learning card and handoff, and replace only the body.
    before = next(b for b in topic["blocks"] if b["type"] == "idcard")
    after = next(b for b in topic["blocks"] if b["type"] == "handoff")
    topic["blocks"] = [before, *blocks, after]


def session1(t: dict[str, dict]) -> None:
    a, b, c = (t[f"hn01-T0{i}"] for i in (1, 2, 3))
    skull = image(b, "hn01_lec_p04_skull")
    # The first run moves this figure from topic 2 to topic 3.
    vault = next(x for topic in (b, c) for x in topic["blocks"]
                 if x.get("asset", "").endswith("hn01_lec_p04_vault.jpeg"))
    facial, hyoid, neck = (image(c, name) for name in ("hn01_lec_p05_facial", "hn01_lec_p05_hyoid", "hn01_lec_p05_hyoidneck"))
    category_table = next(x for x in c["blocks"] if x["type"] == "table")
    wrap(a, [
        {"type":"callout", "kind":"info", "title":"شناسنامهٔ جزوهٔ اصلی", "text":"علوم تشریح سر و گردن؛ استاد خدیجه میرزایی؛ پزشکی مهر ۱۴۰۴، دانشگاه علوم پزشکی بندرعباس؛ گروه جزوه نویسی A. جلسه اول: بررسی استخوان های جمجمه. گروه A: نرگس بنایی، پارسا پورشهابی، وحید رحمانیان، عبدالله دردری، طاها سالار حسینی، عطیه سالاری، آریا امیری زاده، محمد نصیری، پوریا عبداللهی.", "src":"جزوهٔ درس، ص ۱–۲"},
        lecture("این جزوه رو ما تو اسفند ۱۴۰۴ همزمان با جنگ و قطعی اینترنت، با حداقل امکانات درست کردیم اگر کم و کاستی ای بود به بزرگی خودتون ببخشید", 2),
        heading("قسمت محوری (Axial Skeleton)"),
        lecture("مجموعه استخوان هایی هستند که در مرکز قرار گرفته اند. شامل: جمجه، استخوان هیوئید، ستون مهره ها، عناصری که به ستون مهره ها متصل هست مانند دنده ها و جناغ", 3),
        image(a, "hn01_lec_p03_axial"),
        heading("قسمت ضمیمه (Appendicular Skeleton)"),
        lecture("شامل: اندام های فوقانی و تحتانی که به سیستم جانبی اضافه شده اند", 3),
        image(a, "hn01_lec_p03_append"),
    ])
    wrap(b, [
        heading("skull"),
        lecture("جمجمه که در بالای اسکلت محوری قرار گرفته و از ارگان های مهمی مثل حواس ویژه حفاظت می کند. مانند حس بینایی، حس بویایی، حس چشایی و حس شنوایی. همچنین قسمت ابتدایی دستگاه گوارش و دستگاه تنفسی در جمجمه قرار دارند.", 4),
        skull,
        lecture("جمجمه محیطی را برای چسبیدن عضلات ایجاد می کند که این عضلات در ناحیه صورت و گردن قرار گرفتند.", 4),
        lecture("و در جمجمه استخوان های پهنی قرار گرفته که دارای 2 صفحه استخوان متراکم که بین آن دو استخوان اسفنجی قرار دارد و مغز استخوان آن در خونسازی در افراد جوان نقش دارد.", 4),
        lecture("استخوان های جمجمه 22 عدد هستند ولی اگر استخوانچه های گوش را به آن اضافه کنیم 28 عدد می شوند.", 4),
        lecture("پس از متلاشی شدن جسد بافت نرم آنها از بین می رود و استخوانچه های گوش از جمجمه جدا می شوند، به همین علت برخی آنها را جز استخوان های جمجمه حساب نمی کنند.", 4),
        lecture("استخوان های جمجمه شامل استخوان هایی هست که در ناحیه سر و صورت قرار گرفته اند.", 4),
    ])
    wrap(c, [
        heading("استخوان های ناحیه سر (cranial vault bones)"),
        lecture("4 عدد استخوان فرد از قسمت قدام به خلف شامل: پس سری (Occipital)، شاپره ای (Sphenoid)، پرویزنی (Ethmoid)، پیشانی (Frontal)", 4),
        vault,
        lecture("2 جفت هم استخوان زوج شامل: (Temporal) در طرفین و پایین / (Parietal) در طرفین و بالا", 5),
        heading("Facial bones (استخوان های ناحیه صورت)"),
        lecture("6 عدد استخوان زوج شامل: بینی (Nasal) / اشکی (Lacrimal) / گونه ای (Zygomatic) / فک فوقانی (Maxilla) / کامی (Palatine)", 5),
        lecture("2 عدد استخوان فرد شامل: فک تحتانی (Mandible) / تیغه ای (Vomer)", 5),
        facial,
        {"type": "callout", "kind": "info", "title": "توضیح تکمیلی، جدا از متن صفحهٔ ۵", "text": "در فهرست صفحهٔ ۵ نام پنج نوع استخوان زوج دیده می‌شود؛ کارت مرور صفحهٔ ۲۰ شاخک تحتانی بینی را نیز در دستهٔ استخوان‌های صورت آورده است.", "src": "جزوهٔ درس، ص ۵ و ۲۰"},
        category_table,
        heading("Hyoid bone"),
        lecture("استخوان هیوئید یا لامی شکل، استخوانی U شکل هست که در موازات سومین مهره گردن یا C3 قرار گرفته است. این استخوان دارای 3 قسمت: Body جسم، greater horn شاخ بزرگتر / lesser horn شاخ کوچکتر که محل اتصال عضلات و لیگامان ها هستند", 5),
        hyoid, neck,
    ])


def session2(t: dict[str, dict]) -> None:
    a, b, c, d, e = (t[f"hn02-T0{i}"] for i in (1, 2, 3, 4, 5))
    wrap(a, [lecture("این جلسه درمورد ادامه استخوان های جمجمه که شامل: استخوان قدامی (frontalis)، استخوان گونه ای (zygomatic)، استخوان آهیانه ای (parietal)، استخوان گیجگاهی (temporal)، ادامه نماهای جمجمه که شامل نمای طرفی (temporalis) است.", 3)])
    wrap(b, [
        heading("Zygomatic bone/Malar"),
        lecture("به استخوان zygomatic استخوان malar هم گفته میشود اما با molar (دندان آسیاب) تفاوت دارد. استخوان زایگوماتیک از استخوان های زوج صورت هست و در تشکیل برجستگی گونه شرکت دارد. این استخوان در تشکیل کف و جدار خارجی کاسه چشم (orbit) و در تشکیل حفرات temporal و infratemporal شرکت می کند. همچنین در تکمیل قوس گونه هم مشارکت دارد.", 3),
        image(b, "hn02_lec_p03_zygo"),
        lecture("این استخوان دارای سه سطح و پنج کنار و دو زائده است. سطوح آن شامل سطح فاسیال یا لترال و سطح کاسه چشمی (orbital) و temporal و همچنین به واسطه زائده گونه ای سطح infratemporal است. کناره ها پنج عدد هستند که شامل قدامی فوقانی (anterosuperior) و قدامی تحتانی (anteroinfrior) و خلفی فوقانی (posterosuperior) و خلفی تحتانی (posteroinferior) و خلفی داخلی (posteromedial) میباشد.", 3),
        lecture("این استخوان در کنار قدامی فوقانی در تشکیل حاشیه خارجی و تحتانی کاسه چشم شرکت می کند و همچنین سطح فاسیا را از سطح کاسه چشم جدا میکند. این استخوان در کنار قدامی تحتانی خشن است و با زائده zygomatic با استخوان maxilla مفصل میشود. کنار خلفی داخلی قسمتی از آن در بالا با بال بزرگ استخوان پروانه یا sphenoid مفصل میشود. و در پایین هم با صفحه orbital از استخوان فک فوقانی (maxilla) مفصل میشود.", 3),
    ])
    wrap(c, [
        lecture("این استخوان دارای دو زائده است: زائده zygomatic و زائده frontal که با زائده zygomatic از استخوان frontal با هم مفصل میشوند و درز frontozygomatic را تشکیل میدهد. درز frontozygomatic به عنوان یک لندمارک و از روی پوست به صورت تو رفتگی مشخص میشود.", 4),
        image(c, "hn02_lec_p04_lat"),
        lecture("یک سانتی متر پایین تر از درز frontozygomatic در داخل کاسه چشم تکمه ویتنال (Whitnalls tubercle) وجود دارد که به آن رباط پلکی طرفی (lateral palpebral ligament) و بخشی از آپونوروز عضله بالابرنده پلک فوقانی (Levator palpebrae superioris) و suspensory ligament متصل است.", 4),
        lecture("از درز frontozygomatic به سمت پایین marginal tubercle وجود دارد که فاسیا عضله temporalis به این قسمت متصل میشود.", 4),
        image(c, "hn02_lec_p04_whitnall"),
    ])
    wrap(d, [
        heading("Zygomatic arch"),
        lecture("زائده temporal به سمت عقب رفته و انتهای آن مضرس و محدب هست و با زائده zygomatic از استخوان temporal که انتهای آن هم مضرس و محدب است با هم مفصل میشوند و قوس گونه ای (zygomatic arch) را تشکیل میدهند.", 4),
        image(d, "hn02_lec_p04_arch"),
        lecture("این قوس دارای دو کنار هست: کنار فوقانی و تحتانی. کنار فوقانی آزاد است و به کنار تحتانی عضله جونده متصل میشود. قوس گونه یک شاخص یا لندمارک هست برای تشخیص حفره temporal که در بالای قوس گونه قرار میگیرد و حفره infratemporal که در زیر قوس گونه ای قرار میگیرد.", 4),
    ])
    wrap(e, [
        heading("Foramen"), image(e, "hn02_lec_p05_foramina"),
        lecture("استخوان دارای سوراخ (foramen) هایی است که بر روی سطوح آن قرار گرفته.", 5),
        lecture("Zygomaticofacial foramen سوراخی است که بر روی سطح facial قرار گرفته است و عصب zygomaticofacial nerve از آن عبور میکند.", 5),
        lecture("سوراخ گونه-کاسه چشمی (zygomaticoorbital foramen) که از آن عصب zygomaticotemporal nerve عبور میکند.", 5),
        lecture("از سوراخ گونه ای-گیجگاهی (zygomaticotemporal foramen) نیز عصب zygomatic و temporal عبور میکند.", 5),
        lecture("لازم به ذکر است عصب zygomaticotemporal و zygomaticofacial ادامه عصب zygomatic هستند که این عصب از عصب maxillary یا دومین شاخه از عصب پنج مغزی (trigeminal ganglion) مبدأ میگیرد.", 5),
        {"type": "callout", "kind": "info", "title": "یادداشت برای بازبینی علمی", "text": "عبارت‌های مربوط به مسیر اعصاب در این قسمت همان بیان منبع‌اند و لازم است جداگانه با مرجع و نظر متخصص بررسی شوند؛ در متن درس دست برده نشده است.", "src": "جزوهٔ درس، ص ۵"},
    ])


def main() -> None:
    for n, apply in ((1, session1), (2, session2)):
        files = [CONTENT / f"hn0{n}_{part}.json" for part in ("a", "b")]
        docs = [json.loads(path.read_text(encoding="utf-8")) for path in files]
        topics = indexed([t for doc in docs for t in doc])
        apply(topics)
        for topic in topics.values():
            for block in topic["blocks"]:
                if block.get("type") in {"p", "ul", "ol", "table", "callout"}:
                    src = block.get("src", "")
                    if src and not src.startswith("متن جزوهٔ درس") and "بازنویسی یا توضیح تکمیلی" not in src:
                        block["src"] = src + " · بازنویسی یا توضیح تکمیلی"
                elif block.get("type") == "plate":
                    text = block.get("fa_text", "")
                    if text and not text.startswith("توضیح تکمیلی تصویر:"):
                        block["fa_text"] = "توضیح تکمیلی تصویر: " + text
        for path, doc in zip(files, docs):
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"session {n}: opening pages reconciled; remaining topics still require review")


if __name__ == "__main__":
    main()
