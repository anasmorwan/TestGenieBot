
# quiz_generation.py
from bot.bot_instance import bot
from services.quiz_service import generate_quizzes_from_text

def handle_file_upload(chat_id, file_path, user_id):
    content = extract_text(file_path)  # يمكنك استدعاء services.content_parser
    quizzes = generate_quizzes_from_text(content, user_id)
    # إرسال رسالة للمستخدم
    bot.send_message(chat_id, f"تم توليد {len(quizzes)} سؤال!")






#----------------

def process_message(msg, message_id=None, chat_id=None):
    logging.info("process_message enter: uid=%s type=%s", msg.from_user.id, msg.content_type)
    content_type = msg.content_type
    username = msg.from_user.username or "بدون اسم مستخدم"
    uid = msg.from_user.id
    file_id = getattr(getattr(msg, 'document', None), 'file_id', None)

    
    state = user_states.get(int(uid))
    
    
        if state is None:
        # يمكن الرد للتجربة فقط أثناء الديباغ
        # bot.send_message(uid, f"DEBUG: no state set (you are {uid})")
        return
    
    
    
    if content_type:
            
        if not is_file_size_allowed(bot, file_id):
            bot.send_message(uid, " الملف كبير جدًا، الحد 5 ميغابايت.")
            return

        path = save_file(uid, file_name, file_data)
        content, coverage = extract_text_from_file(bot, msg, path, chat_id=chat_id, message_id=message_id)
        quizzes = generate_quizzes_from_text(content, user_id=uid, num_quizzes=num_quizzes)

        if isinstance(quizzes, list) and len(quizzes) > 0:
                
            try:
                print(f"تم توليد {len(quizzes)} سؤالا")
            # تخزين الاختبار أولاً
                quiz_code = store_quiz(uid, quizzes, bot)
                print("[QUIZ] كود الاختبار:", quiz_code)

                if not quiz_code:
                    raise Exception("Failed to store quiz")
                        
                waiting_quiz = loading_msg.message_id
                major = fetch_user_major(uid)
                file_path = user_files[uid]
                level = "متوسط"

                # إرسال رسالة "إختبارك جاهز" مع رابط الاختبار
                quiz_link = f"https://t.me/QuizzyAI_bot?start=quiz_{quiz_code}"
                estimated_time = len(quizzes) * 30

                # إرسال رسالة "إختبارك جاهز" مع رابط الاختبار
                markup = InlineKeyboardMarkup()
                btn = InlineKeyboardButton("فتح الاختبار", url=quiz_link)
                markup.add(btn)

                quiz_msg = (
                "✨✔️ <b>إختبارك جاهز!</b>\n"
                    "──────────────────\n"
                    f"📂 <b>العنوان:</b> {msg.document.file_name}\n\n"
                    f"📋 <b>عدد الأسئلة:</b> {len(quizzes)}\n"
                    f"⏱️ <b>الزمن الكلي:</b> {estimated_time // 60} دقيقة و {estimated_time % 60} ثانية\n"
                    f"🎓 <b>التخصص:</b> {major} \n"
                    "📦 <b>نوع الاختبار:</b> خاص\n\n"
                    f"📉 <b>التغطية:</b> {coverage}\n"
                    "💡 <b>ميزة الشرح:</b> غير متوفرة\n"
                    f"📊 <b>المستوى:</b> {level}\n\n"
                    "❓هل أنت جاهز للإختبار\n"
                    f"👈 <a href=\"{quiz_link}\">اضغط هنا للبدء</a>"
                )
                try:
                    bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
                except Exception as del_err:
                    print(f"لم يتمكن من حذف رسالة التحميل: {del_err}")
                
                bot.send_message(chat_id, quiz_msg, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
                    

                update_top_user(uid, tests=1)
                notify_admin("توليد اختبار", username, uid)
                    
                    
                    