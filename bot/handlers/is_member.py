import telebot
from telebot.types import Message, CallbackQuery
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثال: -1001234567890
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # مثال: @my_channel

bot = telebot.TeleBot(BOT_TOKEN)

def is_user_member(user_id):
    """التحقق من عضوية المستخدم في القناة"""
    try:
        # طريقة 1: باستخدام معرف القناة الرقمي
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        
        # الحالات التي تعتبر المستخدم عضوًا فعالاً
        valid_statuses = ['member', 'creator', 'administrator']
        
        if chat_member.status in valid_statuses:
            return True
        return False
        
    except telebot.apihelper.ApiException as e:
        print(f"خطأ في التحقق من العضوية: {e}")
        return False

def get_channel_invite_link():
    """الحصول على رابط دعوة القناة (اختياري)"""
    try:
        invite_link = bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,  # استخدام واحد فقط
            expire_date=None  # لا تنتهي
        )
        return invite_link.invite_link
    except:
        return CHANNEL_USERNAME if CHANNEL_USERNAME else "رابط القناة"

def check_membership_and_respond(message: Message):
    """التحقق من العضوية والرد بالمطالبة بالانضمام إذا لزم الأمر"""
    user_id = message.from_user.id
    
    if is_user_member(user_id):
        return True
    else:
        invite_link = get_channel_invite_link()
        bot.reply_to(
            message,
            f"❌ عذراً، يجب عليك الاشتراك في قناتنا أولاً!\n\n"
            f"📢 اضغط هنا للانضمام: {invite_link}\n\n"
            f"بعد الانضمام، أعد إرسال الأمر مرة أخرى ✅"
        )
        return False

# مثال: حماية أمر معين
@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    if check_membership_and_respond(message):
        bot.reply_to(message, "مرحباً بك! أنت مشترك في القناة ✅")

# مثال: حماية أمر /poll
@bot.message_handler(commands=['poll'])
def handle_poll(message: Message):
    if not check_membership_and_respond(message):
        return  # يخرج إذا لم يكن مشتركاً
    
    # باقي كود إنشاء الاستطلاع هنا
    bot.reply_to(message, "أنشئ استطلاعك الآن...")

# مثال: حماية callback query (الأزرار)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    # تحقق من العضوية قبل تنفيذ أي شيء
    if not is_user_member(call.from_user.id):
        invite_link = get_channel_invite_link()
        bot.answer_callback_query(
            call.id,
            f"⚠️ يجب الاشتراك في القناة أولاً: {invite_link}",
            show_alert=True
        )
        return
    
    # باقي كود معالجة الأزرار هنا
    bot.edit_message_text(
        "تم التنفيذ بنجاح!",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

# تشغيل البوت
if __name__ == "__main__":
    print("البوت يعمل...")
    bot.infinity_polling()
