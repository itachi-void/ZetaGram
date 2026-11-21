from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.i18n import get_text


def build_pagination_keyboard(
    items_buttons: list,
    current_page: int,
    total_pages: int,
    category_code: str,
    back_callback: str = "earnings_menu",
    lang: str = "ar",
) -> InlineKeyboardMarkup:
    """
    Builds task inline keyboard with localized pagination & action bar.
    """
    keyboard = []

    for btn_row in items_buttons:
        keyboard.append(btn_row)

    if total_pages > 1:
        prev_page = max(1, current_page - 1)
        next_page = min(total_pages, current_page + 1)

        pag_row = [
            InlineKeyboardButton(str(total_pages), callback_data=f"page_{category_code}_{total_pages}"),
            InlineKeyboardButton(">", callback_data=f"page_{category_code}_{next_page}"),
            InlineKeyboardButton(str(current_page), callback_data="ignore"),
            InlineKeyboardButton("<", callback_data=f"page_{category_code}_{prev_page}"),
            InlineKeyboardButton("1", callback_data=f"page_{category_code}_1"),
        ]
        keyboard.append(pag_row)

    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_report"), callback_data="report_issue")])
    keyboard.append([InlineKeyboardButton(get_text(lang, "btn_back"), callback_data=back_callback)])

    return InlineKeyboardMarkup(keyboard)
