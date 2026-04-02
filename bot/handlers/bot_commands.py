from bot.keyboards.more_options_keyboard import more_options_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from storage.messages import get_message
from storage.session_store import user_states


def register(bot):
  
    @bot.message_handler(commands=["menu"])
    def user_info(msg):
        try:
            user_id = msg.from_user.id
            chat_id = msg.chat.id
            
            bot_username = bot.get_me().username
    
            keyboard = more_options_keyboard(bot_username)
            
            
            base_text = get_message("BASE_TEXT")
            menu_text = get_message("MORE")
    
            # النص المتغير (التحية أو مقدمة مخصصة)
            welcome_new_user = "<b>👋 مرحباً بك في TestGenie</b>\n\n"
            welcome_returning_user = "<b>👋 مرحباً بك مجددًا في TestGenie</b>\n\nما الذي ترغب في القيام به اليوم؟\n\n"
        
            #if is_user_exist(chat_id):
            #text = ux_text          
        
        
            #else:    
            #   text = ux_text

            text = menu_text
                
    
            bot.send_message(chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML")

        except Exception as e:
            bot.reply_to(msg, f"❌ الخطأ: {str(e)}")
        



    @bot.message_handler(commands=["send_poll"])
    def user_info(msg):
        try:
            user_id = msg.from_user.id
            chat_id = msg.chat.id
            
                
            
            
            poll_message = get_message("POLL_INST")
                
            
            bot.send_message(chat_id,
            text=poll_message,
            reply_markup=keyboard,
            parse_mode="HTML")

            user_states[user_id] = "awaiting_poll_text"

        except Exception as e:
            bot.reply_to(msg, f"❌ الخطأ: {str(e)}")

      
