from telebot import types

def get_chat_request_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    # تعريف صلاحيات افتراضية (كلها False ثم نغير ما نحتاج)
    # ملاحظة: البراميترز المطلوبة هي 12 تقريباً في النسخ الحديثة
    all_rights = types.ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=True,
        can_post_messages=True, # أهم واحدة للقنوات
        can_edit_messages=True,
        can_pin_messages=True,
        can_manage_topics=False
    )

    request_channel_btn = types.KeyboardButton(
        text="📢 اختر القناة التي تديرها",
        request_chat=types.KeyboardButtonRequestChat(
            request_id=1,
            chat_is_channel=True,
            bot_is_member=True,
            bot_administrator_rights=all_rights # نمرر الكائن كاملاً هنا
        )
    )

    request_group_btn = types.KeyboardButton(
        text="👥 اختر المجموعة التي تديرها",
        request_chat=types.KeyboardButtonRequestChat(
            request_id=2,
            chat_is_channel=False,
            bot_is_member=True,
            bot_administrator_rights=all_rights
        )
    )
    
    markup.add(request_channel_btn, request_group_btn)
    return markup




