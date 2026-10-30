"""Place visually inspected existing reference crops beside relevant topics."""
def before_end(topic_id, block):
 for meta, content in items:
  if meta['topic_id']==topic_id:
   content['blocks'].insert(-1,block);return
 raise ValueError(topic_id)
before_end('hn04-T14',reference('netter','hn03_netter_p34_foramina_superior.jpeg','سوراخ‌های حفرهٔ میانی','نتر، ویراست ۸، پلیت ۳۴، ص ۸۶ فایل PDF','Foramina of Cranial Base','نمای داخلی','تصویر مرجع سوراخ‌ها و اعصاب عبوری را نام‌گذاری می‌کند.',[['سوراخ گرد','Foramen rotundum'],['سوراخ بیضی','Foramen ovale'],['سوراخ خاری','Foramen spinosum']]))
before_end('hn04-T17',reference('netter','hn03_netter_p33_foramina.jpeg','مجرای کاروتید و کانالیکول‌های قاعده','نتر، ویراست ۸، پلیت ۳۳، ص ۸۵ فایل PDF','Foramina of Cranial Base','نمای تحتانی','نتر مسیر کاروتید، شاخهٔ تیمپانیک و شاخهٔ گوشی واگ را در نمای تحتانی نشان می‌دهد.',[['کانال کاروتید','Carotid canal'],['شکاف پتروتیمپانیک','Petrotympanic fissure'],['کانالیکول تمپانیک','Inferior tympanic canaliculus']]))
before_end('hn04-T18',reference('netter','hn03_netter_p33_foramina.jpeg','گذرگاه‌های قاعدهٔ خلفی','نتر، ویراست ۸، پلیت ۳۳، ص ۸۵ فایل PDF','Foramina of Cranial Base','نمای تحتانی','در تصویر مرجع، سوراخ بزرگ، ژوگولار و مجرای هایپوگلوسال برچسب دارند.',[['سوراخ بزرگ','Foramen magnum'],['سوراخ ژوگولار','Jugular foramen'],['کانال هایپوگلوسال','Hypoglossal canal']]))
before_end('hn04-T19',reference('grays','hn01_grays_p860.jpeg','درزهای جمجمه در نمای فوقانی','گری، ویراست ۳، شکل ۸.۲۱، ص ۸۶۰، ص ۸۸ فایل PDF','Superior view of skull','نمای فوقانی','درزهای ساژیتال، کرونال و لامبدوئید را در تصویر مرجع ببینید.',[['درز تاجی','Coronal suture'],['درز ساژیتال','Sagittal suture'],['درز لامبدوئید','Lambdoid suture']]))

before_end('hn04-T12',reference('netter','hn01_netter_p32.jpeg','حدود حفره‌های جمجمه‌ای','نتر، ویراست ۸، پلیت ۳۲، ص ۸۴ فایل PDF','Cranial Base: Superior View','نمای داخلی','سه حفره و حدود استخوانی آن‌ها در تصویر مرجع مشخص شده‌اند.',[['حفره قدامی','Anterior cranial fossa'],['حفره میانی','Middle cranial fossa'],['حفره خلفی','Posterior cranial fossa']]))
before_end('hn04-T16',reference('grays','hn03_grays_p862_fig823.jpeg','کام سخت و قاعدهٔ تحتانی','گری، ویراست ۳، شکل ۸.۲۳، ص ۸۶۲، ص ۹۰ فایل PDF','Inferior view of the skull','نمای تحتانی','کام، سوراخ‌های کامی و نمای قاعده در تصویر مرجع مشخص‌اند.',[['قوس آلوئولار','Alveolar arch'],['کام سخت','Hard palate'],['سوراخ کامی بزرگ','Greater palatine foramen']]))
