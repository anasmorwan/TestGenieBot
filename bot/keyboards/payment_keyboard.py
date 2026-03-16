from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

elif data == "upgrade_account":
    chat_id = callback.from_user.id  # أو msg.chat.id حسب سياقك
    upgrade_text = """
🚀 **ترقية حسابك إلى النسخة المدفوعة**

احصل على تجربة أقوى مع TestGenie Pro ووفّر وقتك في إنشاء الاختبارات.

مع الحساب المدفوع ستحصل على:

✨ إنشاء اختبارات أكثر بدون قيود  
⚡ معالجة أسرع للملفات  
📚 دعم ملفات أكبر ودروس أطول  
🧠 أسئلة أدق وأكثر تنوعاً  
🎯 تجربة تعلم أفضل وأكثر احترافية

💡 مناسب للطلاب والمعلمين وكل من يريد مراجعة الدروس بسرعة.

اضغط على الزر أدناه لفتح جميع الميزات والبدء فوراً.
"""

    # إعداد لوحة الأزرار
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 شراء الاشتراك", callback_data="buy_subscription")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")]
    ])

    # إرسال الرسالة
    bot.send_message(chat_id, upgrade_text, reply_markup=keyboard)
