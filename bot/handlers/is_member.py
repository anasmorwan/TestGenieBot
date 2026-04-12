import telebot
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()


CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثال: -1001234567890
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # مثال: @my_channel



def is_user_member(user_id, bot):

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

def get_channel_invite_link(bot):
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



from telebot import TeleBot
from telebot.types import ChatMemberUpdated


# تخزين معلومات القنوات والمجموعات
joined_chats = {}


def register(bot):
    @bot.chat_member_handler()
    def handle_chat_member(chat_member: ChatMemberUpdated):
        # التحقق من أن البوت هو العضو المضاف
        if chat_member.new_chat_member.user.id == bot.get_me().id:
            chat = chat_member.chat
            chat_id = chat.id
            chat_title = chat.title or chat.username or "بدون اسم"
            chat_type = chat.type  # 'group', 'supergroup', 'channel'
        
            joined_chats[chat_id] = {
                'title': chat_title,
                'type': chat_type,
                'username': chat.username
            }
        
            # طباعة في الكونسول للتأكيد
            print(f"✅ تم الانضمام إلى {chat_type}: {chat_title} (ID: {chat_id})")

