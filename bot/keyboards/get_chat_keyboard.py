from telebot import types

def get_chat_request_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    # طلب القناة
    request_channel_btn = types.KeyboardButton(
        text="📢 اختر القناة التي تديرها",
        request_chat=types.KeyboardButtonRequestChat(
            request_id=1,
            chat_is_channel=True,
            bot_is_member=True, # يجب أن يكون البوت مضافاً مسبقاً
            # حذفنا bot_administrator_rights لتجنب تعقيد المتطلبات
            # وسنكتفي بطلب أن يكون المستخدم هو المشرف
            user_is_creator=False 
        )
    )

    # طلب المجموعة
    request_group_btn = types.KeyboardButton(
        text="👥 اختر المجموعة التي تديرها",
        request_chat=types.KeyboardButtonRequestChat(
            request_id=2,
            chat_is_channel=False,
            bot_is_member=True,
            user_is_creator=False
        )
    )
    
    markup.add(request_channel_btn, request_group_btn)
    return markup
