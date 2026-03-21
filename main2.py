# main.py (مهم: وضع طباعات للتتبع)
import os
from bot.bot_instance import mybot, set_webhook
from bot.handlers import start, text_handler, file_handler, callback_handler, pre_checkout_query_handler, payment_handler
from storage.sqlite_db import init_db
from bot.handlers import poll_answer_handler
from bot import flask
from services.backup_service import restore_if_needed, start_auto_backup
from services.backup_service import is_db_valid, smart_restore
from storage.sqlite_db import force_add_column
import bot.handlers.chat_shared_handler 




print("main starting...", flush=True)

# تسجيل الهاندلرز
start.register(mybot); print("start.register done", flush=True)
text_handler.register(mybot); print("text_handler.register done", flush=True)
file_handler.register(mybot); print("file_handler.register done", flush=True)
callback_handler.register(mybot); print("callback_handler.register done", flush=True)
pre_checkout_query_handler.register_payment(mybot); print("pre_checkout_query_handler.register done", flush=True)
payment_handler.register(mybot); print("payment_handler.register done", flush=True)
poll_answer_handler.register(mybot)
chat_shared_handler.register(mybot)


# سجل الويب هوك داخلياً
flask.register(); print("flask.register done", flush=True)


# ضع webhook ثم شغّل Flask
set_webhook(); print("set_webhook done", flush=True)

# 1. التأكد من وجود ملف قاعدة البيانات أو استعادته فوراً
# لكي يبدأ التطبيق وهو يمتلك "بيانات قديمة" بالفعل
restore_if_needed() 

# 2. التحقق من سلامة الملف المستورد
if not is_db_valid():
    print("قاعدة البيانات تالفة أو غير موجودة، محاولة استعادة ذكية...")
    smart_restore()

# 3. تشغيل التهيئة (بشرط استخدام IF NOT EXISTS)
# وظيفة هذه الخطوة هي "التكملة" فقط؛ إذا كان الملف المستورد قديماً 
# ونقصته جداول جديدة قمت بإضافتها في التحديث الأخير، ستقوم init_db بإنشائها
init_db() 
force_add_column()
print("✅ قاعدة البيانات جاهزة ومحدثة", flush=True)

# 4. بدء النسخ الاحتياطي التلقائي بعد استقرار الحالة
start_auto_backup()



port = int(os.environ.get("PORT", 10000))
print(f"Starting Flask on port {port}", flush=True)
flask.app.run(host="0.0.0.0", port=port)
