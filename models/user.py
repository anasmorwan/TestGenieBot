# user.py
class User:
    def __init__(self, user_id, username, subscription=False):
        self.user_id = user_id
        self.username = username
        self.subscription = subscription