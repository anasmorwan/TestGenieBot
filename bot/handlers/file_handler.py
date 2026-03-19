import os # لا تنسى استيراد مكتبة نظام التشغيل
from services.content_parser import extract_text_from_file
from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager
from services.file_upload import handle_file_upload
# from services.poll_service import send_quiz_message
from bot.keyboards.quiz_buttons import quiz_keyboard
from storage.messages import get_message
from services.refferal import show_referral_message, reward_referral_if_needed
from services.usage import consume_quiz, can_generate
from bot.keyboards.referral_keyboard import referral_keyboard




def register(bot):
    
    def show_referral_message(bot, chat_id):
        keyboard = referral_keyboard()
        bot.send_message(
        chat_id=chat_id, 
        text=get_mesaage("REFFERAL_1"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    @bot.message_handler(content_types=["document"])
    def handle_file(msg):

        user_id = msg.from_user.id
        chat_id = msg.chat.id
        message_id = msg.message_id


        if not can_generate(user_id):
            show_referral_message(bot, chat_id)

        # 👇 استهلك محاولة
        consume_quiz(user_id)
        # 👇 تحقق هل هذا مستخدم جديد تمت دعوته
        reward_referral_if_needed(user_id)

        
        try:
            waiting_msg = bot.send_message(chat_id=chat_id, text=get_message("FILE_QUIZ"))
            path = handle_file_upload(msg)

        except Exception as e:
            print("FILE UPLOAD ERROR:", e, flush=True)

        
        content = None

        try:

            if path:
                content = extract_text_from_file(
                    user_id,
                    bot,
                    msg,
                    path,
                    chat_id,
                    message_id
                )
                if not content:
                    bot.send_message(chat_id, "❌ لم يتمكن النظام من قراءة الملف (OCR فشل).")
                    return
            else:
                print("Error during file upload", flush=True)

            if not content:
                bot.send_message(chat_id, "لم أستطع قراءة الملف.")
                return

            user_instruction = getattr(msg, "caption", None)
            if user_instruction:
                user_instruction = user_instruction.strip()

            
            quizzes = generate_quizzes_from_text(
                content=content,
                user_id=user_id,
                user_instruction=user_instruction
            )

            if not quizzes:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ فشل تحليل النص أو توليد الأسئلة.")
                return

            quiz_code = store_quiz(user_id, quizzes)
            quiz_len = len(quizzes)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=waiting_msg.message_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                reply_markup=quiz_keyboard(quiz_code),
                parse_mode="HTML"
            )
            
        except Exception as e:
            print("File handler ERROR:", e, flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")
        finally:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"تم حذف الملف المؤقت: {path}")
