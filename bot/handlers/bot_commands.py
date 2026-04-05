from bot.keyboards.more_options_keyboard import more_options_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from storage.messages import get_message
from storage.session_store import user_states
from bot.keyboards.constumize_quiz_keyboard import get_testgenie_keyboard

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
        



    @bot.message_handler(commands=["post_poll"])
    def user_info(msg):
        try:
            user_id = msg.from_user.id
            chat_id = msg.chat.id
            
                
            
            
            poll_message = get_message("POLL_INST")
                
            
            bot.send_message(chat_id,
            text=poll_message,
            parse_mode="HTML")

            user_states[user_id] = "awaiting_poll_text"

        except Exception as e:
            bot.reply_to(msg, f"❌ الخطأ: {str(e)}")

      
    @bot.message_handler(commands=["quiz_level"])
    def user_info(msg):
        try:
            user_id = msg.from_user.id
            chat_id = msg.chat.id
            
                
            
            
            quiz_message = get_message("POLL_INST")

            keyboard = get_testgenie_keyboard(selected_level='متوسط', selected_count=10)
            
            bot.send_message(chat_id,
            text=quiz_message,
            reply_markup=keyboard,
            parse_mode="HTML")

            
        except Exception as e:
            bot.reply_to(msg, f"❌ الخطأ: {str(e)}")




import telebot
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

# قائمة معرفات الأدمن
admin_ids = [123, 456]  # استبدل بالأرقام الحقيقية



@bot.message_handler(commands=["knowledge"])
def view_user_knowledge(msg):
    """الأمر: /knowledge <user_id> - يعرض النصوص المحفوظة لمستخدم معين"""
    
    user_id = msg.from_user.id
    
    # التحقق من صلاحيات الأدمن
    if user_id not in admin_ids:
        bot.reply_to(msg, "⛔ هذا الأمر مخصص للأدمن فقط.")
        return
    
    # استخراج معرف المستخدم من الأمر
    parts = msg.text.split()
    
    if len(parts) < 2:
        bot.reply_to(
            msg, 
            "❌ الرجاء إدخال معرف المستخدم.\n\n"
            "مثال: `/knowledge 123456789`",
            parse_mode="Markdown"
        )
        return
    
    # التحقق من أن المعرف رقم
    try:
        target_user_id = int(parts[1])
    except ValueError:
        bot.reply_to(msg, "❌ معرف المستخدم يجب أن يكون رقماً.")
        return
    
    # جلب البيانات من قاعدة البيانات
    try:
        knowledge_data = get_user_knowledge(target_user_id)
        
        if not knowledge_data:
            bot.reply_to(
                msg,
                f"📭 لا توجد نصوص محفوظة للمستخدم `{target_user_id}`.",
                parse_mode="Markdown"
            )
            return
        
        # بناء الرسالة
        message = f"📚 **نصوص المستخدم المحفوظة**\n"
        message += f"👤 **المعرف:** `{target_user_id}`\n"
        message += f"📊 **عدد النصوص:** {len(knowledge_data)}\n"
        message += f"{'─' * 30}\n\n"
        
        for i, record in enumerate(knowledge_data, 1):
            record_id = record.get('id')
            last_text = record.get('last_text', 'لا يوجد نص')
            specialty = record.get('specialty', 'غير محدد')
            updated_at = record.get('updated_at', 'غير معروف')
            

            # ✅ استخدام دالة الاختصار: السطر الأول فقط، بحد أقصى 100 حرف
            last_text = truncate_text(last_text, max_length=100, keep_first_line=True)
            
            message += f"**{i}.** 🆔 سجل رقم: `{record_id}`\n"
            message += f"   📝 **النص:** {last_text}\n"
            message += f"   🏷️ **التخصص:** `{specialty}`\n"
            message += f"   🕒 **آخر تحديث:** `{updated_at}`\n"
            message += f"   {'.' * 20}\n\n"
            
            # تجنب تجاوز حد طول الرسالة (4096 حرف)
            if len(message) > 3800 and i < len(knowledge_data):
                bot.reply_to(msg, message, parse_mode="Markdown")
                message = f"📚 **نصوص المستخدم المحفوظة (تابع)**\n\n"
        
        bot.reply_to(msg, message, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(msg, f"❌ حدث خطأ أثناء جلب البيانات: {str(e)}")


def get_user_knowledge(user_id):
    """جلب جميع النصوص المحفوظة لمستخدم معين"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute("""
            SELECT id, last_text, specialty, updated_at
            FROM user_knowledge 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        rows = c.fetchall()
        
        knowledge_list = []
        for row in rows:
            knowledge_list.append({
                'id': row[0],
                'last_text': row[1],
                'specialty': row[2],
                'updated_at': row[3]
            })
        
        return knowledge_list
        
    except Exception as e:
        print(f"Error in get_user_knowledge: {e}")
        return []
    finally:
        conn.close()
