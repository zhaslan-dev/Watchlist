import urllib.parse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Поиск")],
            [KeyboardButton(text="📋 Очередь")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )

def vote_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍 За", callback_data=f"vote_{item_id}_for"),
                InlineKeyboardButton(text="👎 Против", callback_data=f"vote_{item_id}_against"),
            ]
        ]
    )

def pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"{prefix}{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперёд ▶", callback_data=f"{prefix}{page+1}"))
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def media_links_keyboard(title: str) -> InlineKeyboardMarkup:
    encoded_title = urllib.parse.quote(title)
    buttons = [
        [InlineKeyboardButton(text="Кинопоиск", url=f"https://www.kinopoisk.ru/index.php?kp_query={encoded_title}")],
        [InlineKeyboardButton(text="Иви", url=f"https://www.ivi.ru/search/?q={encoded_title}")],
        [InlineKeyboardButton(text="Okko", url=f"https://okko.tv/search?text={encoded_title}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def search_results_keyboard(movies, page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard = []
    start_index = page * 5 + 1
    for idx, movie in enumerate(movies, start=start_index):
        title = movie.nameRu or movie.nameEn or "Без названия"
        rating = f"⭐ {movie.rating}" if movie.rating else "нет рейтинга"
        button_text = f"{idx}. {title} ({rating})"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"select_movie_{idx}")])

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"search_page_{page-1}"))
    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton(text="Вперёд ▶", callback_data=f"search_page_{page+1}"))
    if pagination_buttons:
        keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)