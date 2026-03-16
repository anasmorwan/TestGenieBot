
# تم النقل
# start.py
from bot.bot_instance import bot
from bot.handlers.menu import send_main_menu
from storage.session_store import user_states

def register(bot):
    print("start handler registered", flush=True)
    
    @bot.message_handler(commands=['start'])
    def unified_start_handler(message):
        # ✅ تجاهل الرسائل في المجموعات
        if message.chat.type != "private":
            return

        chat_id = message.chat.id
        args = message.text.split(maxsplit=1)
        uid = message.from_user.id
    
    
    
        if len(args) > 1:
            param = args[1] if len(args) > 1 else None

            # ✅ إذا كان باراميتر anki_sample
            if param == "anki_sample":
                user_states[chat_id] = "awaiting_anki_file_ai"  # حفظ الحالة
            
                bot.send_message(
                    chat_id=chat_id,
                    text="📝 دعنا نبدأ بإنشاء **ملف بطاقاتك الأول**!\n"
                    "📂 أرسل ملف **PDF** أو **DOCX** أو **PPTX**، أو حتى نصًا مباشرًا 📜.\n"
                    "سيتم توليد ملف **أنكي** مخصص لك تلقائيًا 🎯",
                    parse_mode="Markdown"
                )

                return

            # ✅ معالجة روابط المشاركة مثل: ?start=quiz_ab12cd
            quiz_code = param[5:] if param.startswith("quiz_") else param

            loading_msg = bot.send_message(chat_id, "🧠 جاري تحميل الاختبار...")

            # ✅ محاولة بدء الاختبار
            if not quiz_manager.start_quiz(chat_id, quiz_code, bot):
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=loading_msg.message_id,
                    text="❌ لم يتم العثور على هذا الاختبار أو انتهت صلاحيته."
                )
            return

        # ✅ إذا لم يوجد باراميتر → عرض القائمة الرئيسية
        send_main_menu(chat_id)

