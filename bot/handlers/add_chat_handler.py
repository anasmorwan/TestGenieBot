from telebot import types

def get_chat_request_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    # إنشاء زر لطلب قناة (يكون المستخدم فيها مشرفاً)
    request_channel_btn = types.KeyboardButton(
        text="📢 اختر القناة التي تديرها",
        request_chat=types.KeyboardButtonRequestChat(
            request_id=1,           # معرف للطلب لتعرفه لاحقاً
            chat_is_channel=True,   # نريد قنوات فقط
            user_is_creator=False,  # ليس بالضرورة أن يكون المالك، يكفي أن يكون مشرفاً
            bot_is_member=True,     # يجب أن يكون البوت موجوداً في القناة
            bot_administrator_rights=types.ChatAdministratorRights(can_post_messages=True) # صلاحية النشر
        )
    )
    
    markup.add(request_channel_btn)
    return markup

# عند استقبال القناة المختارة
@bot.message_handler(content_types=['chat_shared'])
def handle_chat_shared(message):
    chat_id = message.chat_shared.chat_id
    request_id = message.chat_shared.request_id
    
    # هنا نقوم بحفظ القناة في قاعدة البيانات كما ناقشنا سابقاً
    # save_channel_to_db(message.from_user.id, chat_id)
    
    bot.send_message(message.chat.id, f"✅ تم ربط القناة بنجاح! معرف القناة هو: {chat_id}")
