"""Transcribe the raster review cards of session 2 (pages 31–33), WIP."""
from __future__ import annotations
import json
from reconcile_hn01_hn02_opening import CONTENT, indexed, lecture, heading
from reconcile_hn01_hn02_middle import select, replace, src_list


def apply(t):
 a=t['hn02-T21']
 replace(a,[
  heading('Review — ۱. استخوان گونه (Zygomatic Bone)'),
  lecture('استخوان زوج که برجستگی گونه را می‌سازد و در تشکیل دیواره خارجی و کف Orbit و حفرات Temporal و Infratemporal نقش دارد.',31),
  heading('ساختار استخوان گونه'),
  lecture('سطوح: Facial (خارجی)، Orbital (داخلی/چشمی)، Temporal (خلفی).',31),
  heading('زوائد مهم'),
  src_list(['Frontal Process: با استخوان فرونتال مفصل می‌شود ← درز Frontozygomatic','Temporal Process: با زائده زایگوماتیک تمپورال ← قوس گونه (Zygomatic Arch)'],31),
  heading('تکمات (Tubercles)'),
  src_list(['Whitnall’s Tubercle: ۱ سانتی‌متر پایین‌تر از درز فرونتوزایگوماتیک','Marginal Tubercle: محل اتصال فاسیای عضله تمپورالیس'],31),
  heading('سوراخ‌ها (Foramina)'),
  src_list(['Zygomaticofacial: عبور عصب و عروق همنام','Zygomaticotemporal: عبور عصب همنام','Zygomaticoorbital: ورود عصب زایگوماتیک (شاخه V₂)'],31),
  lecture('نکته بالینی High Yield: ضربه به گونه ← شکستگی زائده فرونتال و جابجایی استخوان به داخل ← Double Vision (دوبینی) به دلیل جابجایی تکمه ویتنال و کشش Suspensory ligament. همچنین Black Eye در اثر پارگی شریان سوپرااوربیتال و تجمع خون در زیر پوست.',31),
  heading('۲. استخوان فک تحتانی (Mandible)'),
  lecture('بزرگ‌ترین و قوی‌ترین استخوان صورت شامل یک تنه (Body) U-شکل و دو شاخ (Ramus).',31),
  heading('نمای خارجی تنه'),
  src_list(['Symphysis Menti: محل جوش خوردن دو نیمه مندیبل','Mental Protuberance: برجستگی چانه','Mental Foramen: سوراخ چانه‌ای (زیر دندان پرمولار ۲) ← خروج عصب و عروق Mental','Oblique Line: خط مایل از توبرکل منتال به سمت عقب و بالا'],31),
  heading('نمای داخلی تنه'),
  src_list(['Mental Spines (Genial Tubercles): خارهای چانه‌ای (بالایی: Genioglossus، پایینی: Geniohyoid)','Mylohyoid Line: تقسیم تنه به دو حفره: Sublingual fossa (بالای خط ← غده زیرزبانی)، Submandibular fossa (پایین خط ← غده زیر فکی)','Mental Torus: برجستگی استخوانی زیر دندان‌های پرمولار (مزاحم برای دندان مصنوعی)'],31),
  heading('شاخ (Ramus)'),
  lecture('دو زائده در کنار فوقانی که توسط Mandibular Notch جدا می‌شوند:',32),
  src_list(['Coronoid Process (قدامی): اتصال تاندون Temporalis','Condylar Process (خلفی): شامل Head و گردن ← مفصل TMJ با حفره مندیبولار تمپورال','Pterygoid Fovea: گودی در قدام گردن کندیل ← اتصال Pterygoid خارجی'],32),
  heading('سطح داخلی راموس'),
  src_list(['Mandibular Foramen: ورود عصب و عروق Inferior Alveolar','Lingula: تیغه استخوانی در لبه سوراخ ← اتصال Pterygomandibular raphe','Mylohyoid Groove: شیار از زیر لینگولا ← عبور عصب Mylohyoid','Temporal Crest: برجستگی از کرونوئید به سمت مولار ۳','Retromolar Fossa (Trigon): فضای پشت دندان عقل ← لندمارک بلاک عصبی و پروتز'],32),
  heading('۳. نکات تکاملی و تغییرات سنی'),
  src_list(['استخوان‌سازی: دو مرکز اصلی (هفته ۶ در محل سوراخ منتال و هفته ۱۰ در محل دندان‌های پیشین)','جوش خوردن: دو نیمه مندیبل تا سال ۱ یا ۲ بعد از تولد در سمفیز کاملاً جوش می‌خورند','رشد طولانی: افزایش طول با اضافه شدن استخوان به کنار خلفی راموس و بازجذب از کنار قدامی','دوران پیری: با افتادن دندان‌ها، زائده آلوئولار تحلیل ← سوراخ منتال و کانال مندیبولار به کنار فوقانی تنه نزدیک‌تر ← چانه جلوآمده (Prognatism)'],32),
  heading('۴. لندمارک‌های عصبی-عروقی در نمای قدامی'),
  lecture('فاصله از خط وسط (Midline) برای جراحی و بی‌حسی حیاتی است:',32),
  src_list(['Supraorbital Foramen: ≈ ۳ سانتی‌متر از خط وسط','Infraorbital Foramen: ≈ ۲.۵ سانتی‌متر از خط وسط (در راستای دندان پرمولار ۲ فک بالا)','Mental Foramen: ≈ ۲.۵ سانتی‌متر از خط وسط (بین اپکس ریشه دندان‌های ۴ و ۵ فک پایین)'],32),
  heading('مفصل فکی-گیجگاهی (TMJ) و دررفتگی'),
  src_list(['Articular Tubercle: برجستگی مفصلی جلوی حفره فک تحتانی','موقع باز کردن دهان، کندیل فک روی این برجستگی حرکت می‌کند','Postglenoid Tubercle: جلوگیری از عقب‌رفتن بیش از حد فک'],32),
  heading('شکاف‌های حیاتی (Fissures)'),
  lecture('Petrotympanic Fissure: شکاف خاره‌ای-صماخی؛ محل عبور عصب Chorda Tympani (زوج ۷) + شریان صماخی قدامی.',32),
  heading('مثلث فوق مجرایی (Suprameatal Triangle)'),
  lecture('اضلاع: ستیغ سوپراماستوئید (بالا)، مجرای گوش (پایین)، خط عمودی (عقب). اهمیت جراحی: در عمق ۱.۲۵ سانتی‌متری Antrum Mastoid قرار دارد ← دسترسی به عفونت‌های گوش میانی.',32),
  heading('سوراخ استایلوماستوئید (Stylomastoid Foramen)'),
  src_list(['بین زائده استایلوئید و ماستوئید','محل خروج عصب فاسیال (زوج ۷) از جمجمه','نکته تستی: آسیب ← فلج بل (Bell’s Palsy)'],33),
  heading('شیار شریان مننژیال میانی'),
  src_list(['از زاویه قدامی-تحتانی (اسفنوئیدال) شروع می‌شود','پاره شدن در ضربات شقیقه ← خونریزی اپیدورال','لوسید اینتروال واضح (بیداری بین دو حالت کما)'],33),
  heading('Granular Foveolae'),
  src_list(['فرورفتگی‌های اطراف سینوس ساژیتال','جایگاه Arachnoid Granulations','وظیفه: تخلیه CSF به داخل سینوس وریدی'],33),
  heading('خطوط گیجگاهی (Temporal Lines)'),
  src_list(['خط فوقانی: اتصال فاسیای تمپورالیس','خط تحتانی: اتصال عضله تمپورالیس (واضح‌تر)','تشخیص در رادیوگرافی'],33),
  heading('درزها (Sutures) و لندمارک‌ها'),
  src_list(['جلو با فرونتال ← Coronal','عقب با اکسیپیتال ← Lambdoid','بالا با آهیانه مقابل ← Sagittal','Bregma (برخورد ساژیتال و کرونال)','Lambda (برخورد ساژیتال و لامبدوئید)'],33),
  heading('ملاج قدامی (Anterior Fontanelle)'),
  src_list(['بین فرونتال و پاریتال','بزرگ‌ترین ملاج، شکل لوزی','بسته شدن: ۱۸ ماهگی','کاربرد: بررسی فشار داخل جمجمه، لمس نبض'],33),
  heading('ملاج خلفی (Posterior Fontanelle)'),
  src_list(['بین پاریتال و اکسیپیتال','شکل مثلثی','بسته شدن: ۲–۳ ماهگی','تشخیص موقعیت سر در زایمان'],33),
  lecture('دررفتگی حاد TMJ: اگر کندیل فک از روی Articular Tubercle رد شود و بیفتد جلوی آن ← بیمار نمی‌تواند دهانش را ببندد. جااندازی: فشار فک به سمت پایین (برای رد شدن از برجستگی) + سپس هل دادن به عقب. خونریزی اپیدورال: پارگی Middle Meningeal Artery در ضربات شقیقه ← اورژانس جراحی!',33),
 ])


def main():
 paths=[CONTENT/f'hn02_{part}.json' for part in 'ab'];docs=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
 apply(indexed([t for doc in docs for t in doc]))
 for p,doc in zip(paths,docs): p.write_text(json.dumps(doc,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
 print('session 2 review cards transcribed; independent verification remains')

if __name__=='__main__':main()
