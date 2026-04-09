import os # لا تنسى استيراد مكتبة نظام التشغيل
import time
from services.content_parser import extract_text_from_file
from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz, maybe_cleanup
from services.quiz_session_service import quiz_manager
from services.file_upload import handle_file_upload
# from services.poll_service import send_quiz_message
from bot.keyboards.quiz_buttons import quiz_keyboard
from storage.messages import get_message
from services.referral import reward_referral_if_needed
from services.usage import consume_quiz, can_generate, check_subscription_valid
from bot.keyboards.referral_keyboard import referral_keyboard
from services.backup_service import safe_backup, backup_all
from services.backup_service import smart_restore, is_db_valid
from models.pattern_detection import detect_quiz_pattern # استيراد الدالة الأساسية من كودك
from services.user_trap import update_last_active
from bot.keyboards.upsell_keyboard import saved_quiz_upsell


import threading
    


def register(bot):
    
    def show_referral_message(bot, chat_id, user_id):
        keyboard = referral_keyboard(user_id)
        bot.send_message(
        chat_id=chat_id, 
        text=get_message("REFERRAL_1"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    @bot.message_handler(content_types=["document"])
    def handle_file(msg):
        if msg.chat.type != "private":
        
            return

        user_id = msg.from_user.id
        chat_id = msg.chat.id
        message_id = msg.message_id
        update_last_active(user_id)

        try:
            plan = check_subscription_valid(user_id)
            allowed, info = can_generate(user_id)

            if not allowed:
                show_referral_message(bot, chat_id, user_id)
                return  # ❗ هذا هو المفتاح
                
            # 👇 استهلك محاولة
            consume_quiz(user_id)
            # backup_all()
            # 👇 تحقق هل هذا مستخدم جديد تمت دعوته
            reward_referral_if_needed(user_id)
            # backup_all()

        except Exception as e:
            print("File handler ERROR:", e, flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")

        
        try:
            waiting_msg = bot.send_message(chat_id=chat_id, text=get_message("FILE_QUIZ"), parse_mode="HTML")
            path, filename = handle_file_upload(msg)

        except Exception as e:
            print("FILE UPLOAD ERROR:", e, flush=True)

        
        content = None

        try:
            if path == "large_file":
                keyboard = saved_quiz_upsell()
                bot.edit_message_text(
                chat_id=chat_id,
                message_id=waiting_msg.message_id,
                text=get_message("SIZE_LIMIT"),
                reply_markup=keyboard,
                parse_mode="HTML")
                return
                
            if path is not None:
                content = extract_text_from_file(
                    user_id,
                    bot,
                    msg,
                    path,
                    chat_id,
                    message_id
                )
                if content == "ocr_needed":
                    keyboard = saved_quiz_upsell()
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=waiting_msg.message_id,
                        text=get_message("OCR_NEEDED"),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    return
                elif content.startswith("not_supported"):
                    parts = content.split()
                    ext = part[1]
                    keyboard = saved_quiz_upsell()
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=waiting_msg.message_id,
                        text=get_message("OCR_NEEDED"),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    return
            
                
                try:
                    results = detect_quiz_pattern(content)
                    confidence = result.get("confidence", 0)
                    decision = result.get("decision", "review")
                    
                    if decision == "accept":
                        pass
                      #  keyboard = 
                      #  bot.edit_message_text(chat_id, message_id=waiting_msg.message_id, text="💡 هذا النص الملف يحتوي على أسئلة بالفعل، إذا أحببت يمكنني صياغتها لك بتنسيق أسئلة سريعة ؟", reply_markup=keyboard)
                    elif decision == "review":
                        pass
                except:
                    pass
                    
                   
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

            msg_id = waiting_msg.message_id

            quizzes = generate_quizzes_from_text(
            content=content,
            user_id=user_id,
            bot=bot,
            user_instruction=user_instruction,
            msg_id=msg_id
            )
            
            maybe_cleanup()

            if not quizzes:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ فشل تحليل النص أو توليد الأسئلة.")
                return

            quiz_code = store_quiz(user_id, quizzes)
            # backup_all()
            quiz_len = len(quizzes)
            
            
            bot.delete_message(chat_id, message_id=waiting_msg.message_id)
            

            bot.send_message(
                chat_id=chat_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                reply_markup=quiz_keyboard(quiz_code),
                parse_mode="HTML"
            )
            time.sleep(2)
    
            quiz_manager.start_quiz(chat_id, quiz_code, bot, is_shared_user=False)
        
        
        except Exception as e:
            print("File handler ERROR:", e, flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")
        finally:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"تم حذف الملف المؤقت: {path}")
