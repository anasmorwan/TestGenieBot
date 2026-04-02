# session_store.py
user_states = {}
temp_texts = {}


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
