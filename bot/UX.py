import os
import telebot
from telebot.types import ChatPermissions
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
dotenv import load_dotenv
from flask import Flask, render_template
import threading
import logging


# متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(BOT_TOKEN)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
user_states = {}



@bot.message_handler(commands=['start'])
def unified_start_handler(message):
    # ✅ تجاهل الرسائل في المجموعات
    if message.chat.type != "private":
        return

    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    uid = message.from_user.id
    
    
    if not can_generate(uid):
        add_external_user(uid)
    

    if len(args) > 1:
        param = args[1] if len(args) > 1 else None

        # ✅ إذا كان باراميتر anki_sample
        if param == "anki_sample":
            user_states[chat_id] = "awaiting_anki_file_ai"  # حفظ الحالة
            
            bot.send_message(
                chat_id=chat_id,
                "📝 دعنا نبدأ بإنشاء **ملف بطاقاتك الأول**!\n"
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




# ---------------------------------------
# ---------- Main UX ---------------------------------------


def send_main_menu(chat_id, message_id=None):
    BOT_USERNAME = bot.get_me().username
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = [
        InlineKeyboardButton("📄 أنشئ اختبار من ملف", callback_data="go_generate"),
        InlineKeyboardButton("⚡ سؤال سريع", callback_data="quick_quiz"),
        InlineKeyboardButton("⚙️ حسابي", callback_data="go_account_settings"),
    ]

    keyboard.add(*buttons)

    keyboard.add(
        InlineKeyboardButton(
            "➕ أضفني إلى مجموعة",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    )

    text = (
        "👋 مرحباً بك في TestGenie\n\n"
        "حوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
        "📄 أرسل:\n"
        "PDF • DOCX • نص\n\n"
        "وسيحوّله البوت إلى اختبار تلقائياً.\n\n"
        "👇 أو اختر:""
    )

    if message_id:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            chat_id,
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )





@bot.callback_query_handler(func=lambda c: c.data.startswith(("go_", "quick_", "major:", "anki")))
def handle_main_menu(c):
    try:
        bot.answer_callback_query(c.id)
    except:
        pass

    if c.message.chat.type != "private":
        return
    try: 
    
        data = c.data
        chat_id = c.message.chat.id
        message_id = c.message.message_id
        uid = c.from_user.id
        logging.info("Callback received: uid=%s data=%s", uid, data)



        if data == "go_generate":
            user_states[uid] = "awaiting_file"

            sent_msg = bot.edit_message_text(
                    f"الآن أرسل ملف (PDF/DOCX/TXT) أو نصًا مباشرًا لتوليد اختبارك.",
                    chat_id=chat_id, message_id=message_id, parse_mode="Markdown"
            )
            return



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
                    
                    
                    
@bot.message_handler(content_types=['text', 'document', 'photo'])
def unified_handler(msg):
    uid = int(msg.from_user.id)

    file_id = getattr(getattr(msg, 'document', None), 'file_id', None)

    if msg.chat.type != "private":
        return

    threading.Thread(target=process_wrapper, args=(msg,), daemon=True).start()



def process_wrapper(msg):
    with semaphore:
        process_message(msg)

# ----------------------------
# ----    flask config  ----------------------------

# واجهة Flask للفحص
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
    

# نقطة نهاية الويب هوك
@app.route('/' + os.getenv('BOT_TOKEN'), methods=['POST'])
def webhook_bot():
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    return 'Method Not Allowed', 405


        
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + '/' + BOT_TOKEN)
    logging.info(f"🌍 تم تعيين الويب هوك على: {WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    init_all_dbs()
    insert_sample_quiz_if_not_exists()
    set_webhook()
    port = int(os.environ.get('PORT', 10000))  # Render يستخدم 10000
    app.run(host='0.0.0.0', port=port)





