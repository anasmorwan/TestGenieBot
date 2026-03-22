



def register(bot):

    @bot.message_handler(content_types=["image"])
    def handle_file(msg):
        if msg.chat.type != "private":
        
            return

        user_id = msg.from_user.id
        chat_id = msg.chat.id
        message_id = msg.message_id

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
            maybe_cleanup()

            if not quizzes:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ فشل تحليل النص أو توليد الأسئلة.")
                return

            quiz_code = store_quiz(user_id, quizzes)
            # backup_all()
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
