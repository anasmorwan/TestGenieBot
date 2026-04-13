# session_store.py
user_states = {}

user_texts = {}

user_streak = {}

temp_texts = {}

# bot/handlers/callback_handler.py
user_selections = {}

# bot/handlers/callback_handler.py
user_poll_selections = {}


last_active = {}

# services/quiz_service.py:
user_messages_remaining = {}


# Buffer للتخزين المؤقت
message_buffer = {}  # {chat_id: message_count}
chats_buffer = {}    # {chat_id: {'title': ..., 'username': ..., 'type': ...}}


# إضافة رسالة إلى البافر
def add_to_buffer(chat_id: int, title: str, username: str, chat_type: str):
    with buffer_lock:
        chat_id_str = str(chat_id)
        
        # زيادة عداد الرسائل
        message_buffer[chat_id_str] = message_buffer.get(chat_id_str, 0) + 1
        
        # تخزين معلومات الشات (إذا لم تكن موجودة)
        if chat_id_str not in chats_buffer:
            chats_buffer[chat_id_str] = {
                'title': title,
                'username': username,
                'type': chat_type
            }



def get_state_safe(user_id):
    data = user_states.get(user_id)
    if isinstance(data, dict):
        return data.get('state')
    elif isinstance(data, str):
        return data  # في حالة كانت القيمة نصاً مباشراً مثل "poll"
    return None


def get_chat_title(user_id):
    """
    تجلب chat_title للمستخدم عندما يكون في حالة generate_poll
    
    Args:
        user_id: معرف المستخدم
    
    Returns:
        str: اسم الشات إذا وجد، None إذا لم يوجد أو كان الهيكل نصاً بسيطاً
    """
    user_data = user_states.get(user_id)
    
    # إذا كان user_data قاموساً، حاول جلب chat_title
    if isinstance(user_data, dict):
        return user_data.get('chat_title')
    
    # إذا كان user_data نصاً بسيطاً (مثل "poll") أو أي نوع آخر، يرجع None
    return None
