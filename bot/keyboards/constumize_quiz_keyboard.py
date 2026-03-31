from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_testgenie_keyboard(selected_level='متوسط', selected_count=10):
    """
    Returns InlineKeyboardMarkup for TestGenie test creation
    selected_level: 'متقدم', 'متوسط', 'مبتدئ'
    selected_count: 5, 10, 15
    """
    markup = InlineKeyboardMarkup(row_width=3)

    # Row 1: Levels
    levels = ['متقدم', 'متوسط', 'مبتدئ']
    level_buttons = []
    for level in levels:
        text = f"✅ {level}" if level == selected_level else level
        level_buttons.append(InlineKeyboardButton(text=text, callback_data=f"level_{level}"))
    markup.row(*level_buttons)

    # Row 2: Number of questions
    counts = [15, 10, 5]
    count_buttons = []
    for count in counts:
        text = f"✅ {count} سؤال" if count == selected_count else f"{count} سؤال"
        count_buttons.append(InlineKeyboardButton(text=text, callback_data=f"count_{count}"))
    markup.row(*count_buttons)

    # Row 3: Custom and Pro
    markup.row(
        InlineKeyboardButton(text="⚙️ مخصص", callback_data="count_custom"),
        InlineKeyboardButton(text="🔒 20 سؤال - Pro", callback_data="count_pro")
    )

    # Row 4: Start generation
    markup.row(
        InlineKeyboardButton(text="🚀 ابدأ توليد الاختبار الآن", callback_data="start_test")
    )

    return markup
