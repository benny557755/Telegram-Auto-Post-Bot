import asyncio
import logging
import sqlite3
import pytz
import json  # Poll data သိမ်းရန် JSON လိုအပ်ပါသည်
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot_db import init_db, add_post, get_random_post, mark_as_posted, get_setting, set_setting, delete_single_post_db

# --- CONFIG ---
TOKEN = 'TOKEN'
ADMIN_ID = ID 
CHANNEL_IDS = ['Channel ID '] 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Yangon"))

class Form(StatesGroup):
    waiting_for_schedule = State()
    waiting_for_watermark = State()

# --- DATABASE HELPERS ---
def get_pending_posts():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, caption, file_type FROM posts WHERE is_posted = 0")
    posts = cursor.fetchall()
    conn.close()
    return posts

# --- HANDLERS ---

@dp.message(Command('start'))
async def start_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    kb = [
        [InlineKeyboardButton(text="📊 View Queue", callback_data="view_posts_0")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton(text="🚀 Post Now", callback_data="post_now")],
    ]
    await message.answer("🌟 Ultimate Bot Admin Panel", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- SETTINGS MENU ---
@dp.callback_query(F.data == "settings")
async def settings_menu(callback: types.CallbackQuery):
    del_status = "ON" if get_setting('delete_after_post') == '1' else "OFF"
    schedule = get_setting('post_schedule') or "Not Set (Interval Mode)"
    watermark = get_setting('watermark_text') or "None"
    
    kb = [
        [InlineKeyboardButton(text=f"Delete After Post: {del_status}", callback_data="toggle_delete")],
        [InlineKeyboardButton(text=f"Schedule: {schedule}", callback_data="change_schedule")],
        [InlineKeyboardButton(text=f"Watermark: {watermark}", callback_data="change_watermark")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ]
    await callback.message.edit_text("Bot Settings:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "toggle_delete")
async def toggle_del(callback: types.CallbackQuery):
    current = get_setting('delete_after_post')
    set_setting('delete_after_post', '1' if current == '0' else '0')
    await settings_menu(callback)

@dp.callback_query(F.data == "change_schedule")
async def ask_schedule(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_schedule)
    await callback.message.answer("တင်စေချင်တဲ့ အချိန်တွေကို ၂၄ နာရီ Format နဲ့ ရိုက်ပေးပါ။ (ဥပမာ- 08:00, 19:40)")
    await callback.answer()

@dp.message(Form.waiting_for_schedule)
async def process_schedule(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    set_setting('post_schedule', new_time)
    await state.clear()
    
    scheduler.remove_all_jobs()
    times = new_time.split(",")
    for t in times:
        try:
            h, m = t.strip().split(":")
            scheduler.add_job(auto_post_job, 'cron', hour=int(h), minute=int(m))
        except: pass
    
    await message.answer(f"✅ Schedule Updated: {new_time}")
    await start_cmd(message)

@dp.callback_query(F.data == "change_watermark")
async def ask_watermark(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_watermark)
    await callback.message.answer("Watermark အဖြစ်သုံးမည့် စာသား သို့မဟုတ် Link ပို့ပေးပါ။")
    await callback.answer()

@dp.message(Form.waiting_for_watermark)
async def process_watermark(message: types.Message, state: FSMContext):
    set_setting('watermark_text', message.text.strip())
    await state.clear()
    await message.answer(f"✅ Watermark Updated: {message.text}")
    await start_cmd(message)

# --- VIEW QUEUE ---
@dp.callback_query(F.data.startswith("view_posts_"))
async def view_posts(callback: types.CallbackQuery):
    posts = get_pending_posts()
    if not posts:
        return await callback.answer("Queue ထဲမှာ post မရှိသေးပါ!", show_alert=True)

    index = int(callback.data.split("_")[2])
    index = index % len(posts)
    
    post_id, file_id, caption, f_type = posts[index]
    total = len(posts)
    
    nav_kb = [
        [InlineKeyboardButton(text="🗑 Delete This Post", callback_data=f"delete_post_{post_id}")],
        [InlineKeyboardButton(text="⬅️ Previous", callback_data=f"view_posts_{index - 1}"),
         InlineKeyboardButton(text="➡️ Next", callback_data=f"view_posts_{index + 1}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ]
    
    msg_text = f"Post {index + 1}/{total} | Type: {f_type.upper()}\n\n{caption or ''}"

    try:
        if f_type == 'album':
            m_type, m_id = file_id.split(",")[0].split("|")
            if m_type == 'photo': await callback.message.answer_photo(m_id, caption=msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
            else: await callback.message.answer_video(m_id, caption=msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
        elif f_type == 'photo': await callback.message.answer_photo(file_id, caption=msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
        elif f_type == 'video': await callback.message.answer_video(file_id, caption=msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
        elif f_type == 'poll':
            poll_data = json.loads(file_id)
            await callback.message.answer(f"🗳 [POLL]: {poll_data['question']}\n\n{msg_text}", reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
        else: await callback.message.answer(msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb))
        await callback.message.delete()
    except: await callback.answer("Preview Error")

@dp.callback_query(F.data.startswith("delete_post_"))
async def delete_post_handler(callback: types.CallbackQuery):
    delete_single_post_db(callback.data.split("_")[2])
    await callback.answer("Deleted!")
    await view_posts(callback)

# --- UPLOADS ---
album_data = {}

@dp.message(F.from_user.id == ADMIN_ID, F.poll)
async def handle_poll(message: types.Message):
    poll = message.poll
    poll_dict = {
        "question": poll.question,
        "options": [o.text for o in poll.options],
        "is_anonymous": poll.is_anonymous,
        "type": poll.type,
        "allows_multiple_answers": poll.allows_multiple_answers,
        "correct_option_id": poll.correct_option_id
    }
    add_post(json.dumps(poll_dict), message.caption or "", "poll")
    await message.reply("✅ Poll added to queue!")

@dp.message(F.from_user.id == ADMIN_ID, F.media_group_id)
async def handle_albums(message: types.Message):
    mg_id = message.media_group_id
    if mg_id not in album_data:
        album_data[mg_id] = {"media": [], "caption": message.caption}
    
    if message.photo: album_data[mg_id]["media"].append(f"photo|{message.photo[-1].file_id}")
    elif message.video: album_data[mg_id]["media"].append(f"video|{message.video.file_id}")
    
    await asyncio.sleep(2) 
    if mg_id in album_data:
        add_post(",".join(album_data[mg_id]["media"]), album_data[mg_id]["caption"], "album")
        del album_data[mg_id]
        await message.reply("✅ Album added!")

@dp.message(F.from_user.id == ADMIN_ID)
async def handle_single_uploads(message: types.Message):
    if message.text and message.text.startswith('/'): return
    file_id, f_type, caption = message.text, 'text', message.caption or message.text
    if message.photo: file_id, f_type = message.photo[-1].file_id, 'photo'
    elif message.video: file_id, f_type = message.video.file_id, 'video'
    add_post(file_id, caption, f_type)
    await message.reply(f"✅ Saved as {f_type}!")

# --- AUTO POST ---
async def auto_post_job():
    post = get_random_post()
    if not post: return
    post_id, file_id, caption, f_type = post
    watermark = get_setting('watermark_text') or ""
    final_cap = (caption or "") + f"\n\n{watermark}"

    for channel in CHANNEL_IDS:
        try:
            if f_type == 'album':
                media = []
                for i, p in enumerate(file_id.split(",")):
                    m_t, m_i = p.split("|")
                    cap = final_cap if i == 0 else ""
                    media.append(InputMediaPhoto(media=m_i, caption=cap) if m_t == 'photo' else InputMediaVideo(media=m_i, caption=cap))
                await bot.send_media_group(channel, media)
            elif f_type == 'photo': await bot.send_photo(channel, file_id, caption=final_cap)
            elif f_type == 'video': await bot.send_video(channel, file_id, caption=final_cap)
            elif f_type == 'poll':
                pd = json.loads(file_id)
                await bot.send_poll(
                    chat_id=channel,
                    question=pd['question'],
                    options=pd['options'],
                    is_anonymous=pd['is_anonymous'],
                    type=pd['type'],
                    allows_multiple_answers=pd['allows_multiple_answers'],
                    correct_option_id=pd['correct_option_id']
                )
            else: await bot.send_message(channel, final_cap)
        except Exception as e: logging.error(f"Post error: {e}")
    mark_as_posted(post_id)

@dp.callback_query(F.data == "post_now")
async def manual_post(callback: types.CallbackQuery):
    await auto_post_job()
    await callback.answer("Posted!")

@dp.callback_query(F.data == "back_home")
async def go_back_home(callback: types.CallbackQuery):
    await callback.message.delete()
    await start_cmd(callback.message)

async def main():
    init_db()
    await bot.set_my_commands([BotCommand(command="start", description="Menu")])
    
    schedule_str = get_setting('post_schedule')
    if schedule_str:
        for t in schedule_str.split(","):
            try:
                h, m = t.strip().split(":")
                scheduler.add_job(auto_post_job, 'cron', hour=int(h), minute=int(m))
            except: pass
    else:
        limit = int(get_setting('daily_limit') or 5)
        scheduler.add_job(auto_post_job, 'interval', hours=24/limit)
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())