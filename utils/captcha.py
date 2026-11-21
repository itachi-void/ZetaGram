import io
import time
import random
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CAPTCHA_TTL_SECONDS
from utils.i18n import get_text
from utils.html_utils import utcnow


def _load_captcha_font(size: int = 42):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def generate_image_captcha(lang: str = "ar") -> Tuple[io.BytesIO, int, List[int], str]:
    """
    Generate a noisy PNG math captcha image (320x120) and 4 shuffled answer choices.
    Returns: (png_bytes_io, answer, options, caption_html)
    """
    op = random.choice(["+", "-"])
    if op == "+":
        a = random.randint(2, 19)
        b = random.randint(2, 19)
        answer = a + b
    else:
        a = random.randint(10, 29)
        b = random.randint(1, a - 1)
        answer = a - b

    wrong = set()
    while len(wrong) < 3:
        delta = random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5, -5])
        cand = answer + delta
        if cand >= 0 and cand != answer:
            wrong.add(cand)

    options = list(wrong) + [answer]
    random.shuffle(options)

    width, height = 320, 120
    bg_color = (random.randint(235, 250), random.randint(235, 250), random.randint(240, 255))
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    for _ in range(380):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        c = (random.randint(150, 225), random.randint(150, 225), random.randint(150, 225))
        draw.point((x, y), fill=c)

    for _ in range(random.randint(5, 8)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        lc = (random.randint(110, 190), random.randint(110, 190), random.randint(110, 190))
        draw.line([(x1, y1), (x2, y2)], fill=lc, width=random.randint(1, 3))

    font = _load_captcha_font(42)
    expr = f"{a} {op} {b} = ?"
    start_x = 28
    for ch in expr:
        if ch == " ":
            start_x += 12
            continue
        y_off = random.randint(28, 44)
        txt_color = (random.randint(15, 70), random.randint(20, 80), random.randint(40, 120))
        draw.text((start_x, y_off), ch, fill=txt_color, font=font)
        try:
            bbox = draw.textbbox((0, 0), ch, font=font)
            cw = max(16, bbox[2] - bbox[0])
        except Exception:
            cw = 22
        start_x += cw + random.randint(2, 6)

    img = img.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    caption = get_text(lang, "captcha_image_caption")
    return buf, answer, options, caption


def build_captcha_markup(options: List[int], lang: str = "ar") -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for opt in options:
        row.append(InlineKeyboardButton(str(opt), callback_data=f"captcha_val_{opt}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append(
        [InlineKeyboardButton(get_text(lang, "captcha_btn_refresh"), callback_data="captcha_refresh")]
    )
    return InlineKeyboardMarkup(keyboard)


async def send_captcha_challenge(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    lang: str = "ar",
    locked_until=None,
) -> bool:
    """Send an image captcha challenge (or lock notice if captcha-locked)."""
    user_id = update.effective_user.id
    now = utcnow()

    if locked_until and now < locked_until:
        rem_secs = (locked_until - now).total_seconds()
        mins = max(1, int(rem_secs // 60) + (1 if rem_secs % 60 > 0 else 0))
        lock_msg = get_text(lang, "captcha_locked", mins=mins)
        if update.callback_query:
            try:
                await update.callback_query.answer(
                    get_text(lang, "captcha_locked_alert"), show_alert=True
                )
            except Exception:
                pass
        await context.bot.send_message(chat_id=user_id, text=lock_msg, parse_mode="HTML")
        return False

    buf, answer, options, caption = generate_image_captcha(lang)
    context.user_data["captcha_answer"] = int(answer)
    context.user_data["captcha_expires_at"] = float(time.time() + CAPTCHA_TTL_SECONDS)

    markup = build_captcha_markup(options, lang=lang)
    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception:
            pass

    await context.bot.send_photo(
        chat_id=user_id,
        photo=buf,
        caption=caption,
        parse_mode="HTML",
        reply_markup=markup,
    )
    return True
