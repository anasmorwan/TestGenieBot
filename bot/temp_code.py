import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثال: -1001234567890

bot = telebot.TeleBot(BOT_TOKEN)

# --- بيانات مؤقتة للمستخدمين ---
user_data = {}  # هيكل: {user_id: {"content": str, "buttons": list, "step": str}}
def register():
    # --- Step 1: بدء الأمر ---
    @bot.message_handler(commands=['create_post'])
    def cmd_create_post(message: Message):
        user_id = message.from_user.id
        # إعادة تعيين بيانات المستخدم
        user_data[user_id] = {
            "content": "",
            "buttons": [],
            "step": "waiting_content"
        }
        bot.reply_to(
            message,
            "📝 أرسل نص المنشور بتنسيق Markdown.\n"
            "مثال:\n"
            "*عنوان عريض*\n"
            "_نص مائل_\n"
            "[رابط](https://example.com)\n\n"
            "يمكنك استخدام **غامق**، _مائل_، ~~تسطير~~، `كود`، إلخ."
        )

    # --- Step 2: استلام نص المنشور ---
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get("step") == "waiting_content")
    def receive_content(message: Message):
        user_id = message.from_user.id
        user_data[user_id]["content"] = message.text
        user_data[user_id]["step"] = "adding_buttons"
    
        # عرض قائمة إضافة زر
        show_button_menu(message.chat.id, user_id)

    def show_button_menu(chat_id, user_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("➕ إضافة زر رابط", callback_data="add_url_button"),
            InlineKeyboardButton("➕ إضافة زر كود回调", callback_data="add_callback_button"),
            InlineKeyboardButton("✅ إنهاء وإنشاء المنشور", callback_data="finish_post"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_post")
        )
        # عرض الأزرار المضافة حتى الآن
        buttons = user_data[user_id]["buttons"]
        if buttons:
            summary = "🔘 *الأزرار المضافة حالياً:*\n"
            for i, btn in enumerate(buttons, 1):
                summary += f"{i}. {btn['text']} → {btn['type']}: {btn['data']}\n"
            bot.send_message(chat_id, summary, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ لم تقم بإضافة أي زر بعد. يمكنك إضافة أزرار أو النشر بدون أزرار.")
    
        bot.send_message(chat_id, "اختر إجراء:", reply_markup=markup)

    # --- Step 3: معالجة اختيار نوع الزر ---
    @bot.callback_query_handler(func=lambda call: call.data in ["add_url_button", "add_callback_button"])
    def ask_button_text(call: CallbackQuery):
        user_id = call.from_user.id
        if user_id not in user_data:
            bot.answer_callback_query(call.id, "انتهت الجلسة، أعد استخدام /create_post")
            return
    
        button_type = "url" if call.data == "add_url_button" else "callback"
        user_data[user_id]["temp_button"] = {"type": button_type}
        user_data[user_id]["step"] = "waiting_button_text"
    
        bot.edit_message_text(
            "✏️ أرسل النص الذي سيظهر على الزر (يمكنك استخدام إيموجي مثل 📢 👍 ✅):",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)

    # --- Step 4: استلام نص الزر ---
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get("step") == "waiting_button_text")
    def receive_button_text(message: Message):
        user_id = message.from_user.id
        button_text = message.text.strip()
        if not button_text:
            bot.reply_to(message, "❌ النص لا يمكن أن يكون فارغاً، أعد المحاولة:")
            return
    
        user_data[user_id]["temp_button"]["text"] = button_text
    
        # طلب الرابط أو الكود حسب النوع
        btn_type = user_data[user_id]["temp_button"]["type"]
        if btn_type == "url":
            bot.reply_to(message, "🔗 أرسل الرابط (يبدأ بـ http:// أو https://):")
            user_data[user_id]["step"] = "waiting_button_url"
        else:
            bot.reply_to(message, "📞 أرسل كود الـ callback (مثال: like_123, open_menu):")
            user_data[user_id]["step"] = "waiting_button_callback"

    # --- Step 5a: استلام الرابط ---
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get("step") == "waiting_button_url")
    def receive_button_url(message: Message):
        user_id = message.from_user.id
        url = message.text.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            bot.reply_to(message, "❌ الرابط غير صالح، يجب أن يبدأ بـ http:// أو https://\nأعد المحاولة:")
            return
        
        user_data[user_id]["temp_button"]["data"] = url
        # حفظ الزر النهائي
        final_button = {
            "text": user_data[user_id]["temp_button"]["text"],
            "type": "url",
            "data": url
        }
        user_data[user_id]["buttons"].append(final_button)
        del user_data[user_id]["temp_button"]
        user_data[user_id]["step"] = "adding_buttons"
    
        bot.reply_to(message, "✅ تم إضافة الزر بنجاح!")
        show_button_menu(message.chat.id, user_id)

    # --- Step 5b: استلام كود callback ---
    @bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get("step") == "waiting_button_callback")
    def receive_button_callback(message: Message):
        user_id = message.from_user.id
        callback_data = message.text.strip()
        if not callback_data:
            bot.reply_to(message, "❌ الكود لا يمكن أن يكون فارغاً، أعد المحاولة:")
            return
    
        user_data[user_id]["temp_button"]["data"] = callback_data
        final_button = {
            "text": user_data[user_id]["temp_button"]["text"],
            "type": "callback",
            "data": callback_data
        }
        user_data[user_id]["buttons"].append(final_button)
        del user_data[user_id]["temp_button"]
        user_data[user_id]["step"] = "adding_buttons"
    
        bot.reply_to(message, "✅ تم إضافة الزر بنجاح!")
        show_button_menu(message.chat.id, user_id)

    # --- Step 6: إنهاء وإنشاء المنشور (معاينة) ---
    @bot.callback_query_handler(func=lambda call: call.data == "finish_post")
    def preview_post(call: CallbackQuery):
        user_id = call.from_user.id
        if user_id not in user_data or not user_data[user_id]["content"]:
            bot.answer_callback_query(call.id, "لا يوجد محتوى للمنشور، أعد استخدام /create_post")
            return
    
        content = user_data[user_id]["content"]
        buttons = user_data[user_id]["buttons"]
    
        # بناء لوحة المفاتيح
        markup = InlineKeyboardMarkup(row_width=2)
        for btn in buttons:
            if btn["type"] == "url":
                markup.add(InlineKeyboardButton(btn["text"], url=btn["data"]))
            else:
                markup.add(InlineKeyboardButton(btn["text"], callback_data=btn["data"]))
    
        # إرسال المعاينة للمستخدم نفسه
        try:
            bot.send_message(
                call.message.chat.id,
                f"📢 *معاينة المنشور:*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=markup if buttons else None
            )
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ خطأ في تنسيق Markdown: {e}\nيرجى التأكد من صحة التنسيق.")
            return
    
        # سؤال تأكيد
        confirm_markup = InlineKeyboardMarkup(row_width=2)
        confirm_markup.add(
            InlineKeyboardButton("✅ نشر الآن", callback_data="confirm_publish"),
            InlineKeyboardButton("✏️ تعديل المحتوى", callback_data="edit_content"),
            InlineKeyboardButton("🗑 حذف آخر زر", callback_data="remove_last_button"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_post")
        )
        bot.send_message(
            call.message.chat.id,
            "هل أنت راضٍ عن المعاينة؟",
            reply_markup=confirm_markup
        )
        bot.answer_callback_query(call.id)

    # --- تعديل المحتوى ---
    @bot.callback_query_handler(func=lambda call: call.data == "edit_content")
    def edit_content(call: CallbackQuery):
        user_id = call.from_user.id
        user_data[user_id]["step"] = "waiting_content"
        bot.edit_message_text(
            "📝 أرسل النص الجديد للمنشور (Markdown):",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)

    # --- حذف آخر زر ---
    @bot.callback_query_handler(func=lambda call: call.data == "remove_last_button")
    def remove_last_button(call: CallbackQuery):
        user_id = call.from_user.id
        if user_data[user_id]["buttons"]:
            removed = user_data[user_id]["buttons"].pop()
            bot.answer_callback_query(call.id, f"تم حذف الزر: {removed['text']}")
        else:
            bot.answer_callback_query(call.id, "لا يوجد أزرار لحذفها", show_alert=True)
            return
        # إعادة عرض قائمة الأزرار
        show_button_menu(call.message.chat.id, user_id)

    # --- تأكيد النشر في القناة ---
    @bot.callback_query_handler(func=lambda call: call.data == "confirm_publish")
    def publish_to_channel(call: CallbackQuery):
        user_id = call.from_user.id
        content = user_data[user_id]["content"]
        buttons = user_data[user_id]["buttons"]
    
        markup = InlineKeyboardMarkup(row_width=2)
        for btn in buttons:
            if btn["type"] == "url":
                markup.add(InlineKeyboardButton(btn["text"], url=btn["data"]))
            else:
                markup.add(InlineKeyboardButton(btn["text"], callback_data=btn["data"]))
    
        try:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=content,
                parse_mode="Markdown",
                reply_markup=markup if buttons else None
            )
            bot.edit_message_text(
                "✅ تم نشر المنشور بنجاح في القناة!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            # تنظيف البيانات
            del user_data[user_id]
        except Exception as e:
            bot.edit_message_text(
                f"❌ فشل النشر: {e}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        bot.answer_callback_query(call.id)

    # --- إلغاء العملية ---
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_post")
    def cancel_post(call: CallbackQuery):
        user_id = call.from_user.id
        if user_id in user_data:
            del user_data[user_id]
        bot.edit_message_text(
            "❌ تم إلغاء إنشاء المنشور.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)

    # --- معالجة أزرار callback (مثال) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("like_") or call.data == "open_menu")
    def handle_post_buttons(call: CallbackQuery):
        # هنا يمكنك وضع المنطق الخاص بأزرار المنشورات المنشورة
        bot.answer_callback_query(call.id, f"تم الضغط على: {call.data}")
        # مثلاً: تسجيل إعجاب، فتح قائمة، إلخ.

