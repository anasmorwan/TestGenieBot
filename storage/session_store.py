# session_store.py
user_states = {}

def get_state_safe(user_id):
    data = user_stats.get(user_id)
    if isinstance(data, dict):
        return data.get('state')
    elif isinstance(data, str):
        return data  # في حالة كانت القيمة نصاً مباشراً مثل "poll"
    return None


def get_chat_title(user_id):

    user_data = user_stats.get(user_id)
    if isinstance(user_data, dict):
        return user_data.get('chat_title')
    return None
