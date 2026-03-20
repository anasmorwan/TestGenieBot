from services.quiz_session_service import quiz_manager

# تم النقل
# start.py
# bot/handlers/start.py
from bot.handlers.menu import send_main_menu
from storage.session_store import user_states
from services.referral import save_referral
from storage.sqlite_db import get_connection



def register(bot):
    
    @bot.message_handler(commands=['start'])
    def unified_start_handler(message):
        conn = get_connection()
        c = conn.cursor()
        print("/start received:", message.from_user.id, flush=True)
        # ✅ تجاهل الرسائل في المجموعات
        if message.chat.type != "private":
            print("ignored non-private start", flush=True)
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

        
            if param.startswith("ref_"):
                referrer_id = int(args[1].replace("ref_", ""))
                c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
                exists = c.fetchone()

                if not exists:
                    invited_by = None

                # منع self-referral
                if referrer_id != uid:
                    save_referral(referrer_id, invited_by)

                # ✅ إذا لم يوجد باراميتر → عرض القائمة الرئيسية
                send_main_menu(chat_id)
                return


            # ✅ معالجة روابط المشاركة مثل: ?start=quiz_ab12cd
            quiz_code = param[5:] if param.startswith("quiz_") else param

            loading_msg = bot.send_message(chat_id, "🧠 جاري تحميل الاختبار...")

            # ✅ محاولة بدء الاختبار
            if not quiz_manager.start_quiz(chat_id, quiz_code, bot):
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=loading_msg.message_id,
                    text="😵 لم يتم العثور على هذا الاختبار أو انتهت صلاحيته."
                )
            return

        # ✅ إذا لم يوجد باراميتر → عرض القائمة الرئيسية
        send_main_menu(chat_id)





"""
    print("start handler registered", flush=True)
    @bot.message_handler(commands=['start'])
    def unified_start_handler(message):

        print("/start received:", message.from_user.id, flush=True)

        try:
            chat_id = message.chat.id

            print("calling menu...", flush=True)

            send_main_menu(chat_id)

            print("menu sent successfully", flush=True)

        except Exception as e:
            print("ERROR IN START HANDLER:", e, flush=True)
    
"""
