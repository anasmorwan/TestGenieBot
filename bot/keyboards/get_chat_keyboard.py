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
