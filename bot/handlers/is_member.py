import telebot
import os
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import ChatMemberUpdated

# تحميل المتغيرات من ملف .env
load_dotenv()

# تخزين معلومات القنوات والمجموعات
joined_chats = {}


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






def register(bot):
    # جلب جميع المحادثات الحالية عند بدء التشغيل
    def fetch_existing_chats():
        try:
            # الحصول على آخر التحديثات
            updates = bot.get_updates()
            for update in updates:
                if update.chat_member:
                    chat = update.chat_member.chat
                    if chat.type in ['group', 'supergroup', 'channel']:
                        chat_id = chat.id
                        joined_chats[chat_id] = {
                            'title': chat.title or chat.username or "بدون اسم",
                            'type': chat.type,
                            'username': chat.username
                        }
                        print(f"📌 تم تحميل: {chat.title} (ID: {chat_id})")
        except Exception as e:
            print(f"خطأ في جلب المحادثات: {e}")
    
    # استدعاء الجلب عند بدء التشغيل
    fetch_existing_chats()
    
    # متابعة الاستماع للأحداث الجديدة
    @bot.chat_member_handler()
    def handle_chat_member(chat_member: ChatMemberUpdated):
        if chat_member.new_chat_member.user.id == bot.get_me().id:
            chat = chat_member.chat
            chat_id = chat.id
            chat_title = chat.title or chat.username or "بدون اسم"
            chat_type = chat.type
            
            joined_chats[chat_id] = {
                'title': chat_title,
                'type': chat_type,
                'username': chat.username
            }
            print(f"✅ تم الانضمام إلى {chat_type}: {chat_title} (ID: {chat_id})")


