from telebot import types

def register(bot):
    
    # عند استقبال القناة المختارة
    @bot.message_handler(content_types=['chat_shared'])
    def handle_chat_shared(message):
        chat_id = message.chat_shared.chat_id
        request_id = message.chat_shared.request_id
    
        # هنا نقوم بحفظ القناة في قاعدة البيانات كما ناقشنا سابقاً
        # save_channel_to_db(message.from_user.id, chat_id)
    
        bot.send_message(message.chat.id, f"✅ تم ربط القناة بنجاح! معرف القناة هو: {chat_id}")
