import os
import asyncio
import time
import random
import yt_dlp
from flask import Flask
from threading import Thread

# --- EVENT LOOP FIX ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls import filters as ptc_filters
from pytgcalls.types import MediaStream

# ----------------- CONFIGURATION -----------------
API_ID = 38074255  # Apna API ID dalein
API_HASH = "b24d8bf27bba4316a37c4bf2a7e9b9cf"
BOT_TOKEN = "8712882922:AAEpzHdNSgsP60idD50_WcvCcrwzaQzBD2g"
SESSION_STRING = "BQJE948AxjlJfRIp_e9772JU6rn0Dbg5hSr1eqFuZvgG7RG1iHKeZjt1-8k72XDALn_5r4Jx0QXfZROL0ZxwFbi39DNlTQvU0t0dJIvs-SwJTyQmBEixyN2aGDlprrrRpRjdO4IFqPKgf30wj4tgMdWwlfg-6rmhKtQ5dojRcAhdqWXioibbYkB2ox43CfVNwXuK77b02H_LE22GDj5IV6xDVqbNsxcSR6OBXsrhJY11HdJrV5AkAxgbelkB5sWG_6GuiWaK0XD3WAIBoOop8f3vcn3opvO2QqytOTbHWnyuAkDwW3gbTLYfQEXXMZuRIEYyjmw-I0dCjppxB2vB3cjq9361xAAAAAHwf61bAA"
OWNER_ID = 7513729138  # Apna Telegram User ID dalein

# in_memory=True lagaya hai taaki "Database Locked" ka error hamesha ke liye band ho jaye
app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
userbot = Client("Userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(userbot)

boot_time = time.time()
music_queue = {}
playing_now = []  # Naya Smart Tracker (No get_call errors)

# ----------------- SMART SOUNDCLOUD EXTRACTOR -----------------
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 🔥 FIX: Wapas SoundCloud par aaye, par 'official' add kar diya taaki remix na aaye
            search_query = f"scsearch1:{query} official"
            result = ydl.extract_info(search_query, download=False)
            
            if not result or 'entries' not in result or not result['entries']:
                return None, None, None, None, "No results found on SoundCloud."
                
            info = result['entries'][0]
            
            duration_val = int(info.get('duration', 0))
            duration_min = f"{duration_val // 60:02d}:{duration_val % 60:02d}"
            
            thumb = info.get('thumbnail') or "https://telegra.ph/file/86178df6e68ec1421cbff.jpg"
            return info.get('title'), info.get('url'), thumb, duration_min, None
            
    except Exception as e:
        return None, None, None, None, str(e)


# ----------------- UI KEYBOARDS -----------------
def play_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pᴀᴜsᴇ", callback_data="pause"),
            InlineKeyboardButton("▶️ Rᴇsᴜᴍᴇ", callback_data="resume"),
            InlineKeyboardButton("⏭ Sᴋɪᴘ", callback_data="skip")
        ],
        [InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="stop")],
        [InlineKeyboardButton("⚡️ ᴋsʜᴀᴛʀɪʏᴀ ᴏᴘ ⚡️", url="https://t.me/KSHATRIYA_OP")]
    ])

# ----------------- COMMANDS -----------------

# 1. Premium Start Command (Personal Chat Only)
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    bot_info = await client.get_me()
    welcome_text = (
        f"🌟 **Hᴇʟʟᴏ {message.from_user.mention}!** 🌟\n\n"
        "I ᴀᴍ ᴛʜᴇ ⚡️ **KSHATRIYA** ⚡️ Pᴏᴡᴇʀғᴜʟ VC Mᴜsɪᴄ Bᴏᴛ.\n"
        "Eǫᴜɪᴘᴘᴇᴅ ᴡɪᴛʜ Hɪɢʜ-Qᴜᴀʟɪᴛʏ Aᴜᴅɪᴏ, Sᴍᴀʀᴛ Qᴜᴇᴜᴇ & Pʀᴇᴍɪᴜᴍ UI.\n\n"
        "Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴅʀᴏᴘ ᴀ sᴏɴɢ ɴᴀᴍᴇ ᴡɪᴛʜ `/play` ᴛᴏ sᴛᴀʀᴛ ᴛʜᴇ ᴘᴀʀᴛʏ!"
    )
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ➕", url=f"https://t.me/{bot_info.username}?startgroup=true")],
        [InlineKeyboardButton("💥 Dᴇᴠᴇʟᴏᴘᴇʀ 💥", url="https://t.me/KSHATRIYA_OP")]
    ])
    
    banner_url = "https://graph.org/file/1d05566d72e8e5f3d3f77-bf3987635fa4c0ef55.jpg" 
    await message.reply_photo(photo=banner_url, caption=welcome_text, reply_markup=markup)

# ----------------- UPDATED PLAY COMMAND -----------------
@app.on_message(filters.command("play") & filters.group)
async def play_music(client, message):
    chat_id = message.chat.id
    query = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else None
    
    if not query:
        return await message.reply_text("❌ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴏɴɢ ɴᴀᴍᴇ!")
    
    status = await message.reply_text("🔄 **Sᴇᴀʀᴄʜɪɴɢ Aᴜᴅɪᴏ...** 🎵")
    
    # 5 values catch kar rahe hain (Error message ke sath)
    title, stream_url, thumb, duration, error_msg = await asyncio.to_thread(search_youtube, query)
    
    # Agar error aaya, toh chat mein error print hoga!
    if error_msg:
        return await status.edit_text(
            f"❌ **Hᴏsᴛɪɴɢ/Eхᴛʀᴀᴄᴛɪᴏɴ Eʀʀᴏʀ!**\n\n"
            f"**Rᴇᴀsᴏɴ:** `{error_msg}`\n\n"
            f"*(Bhai, isse sabit hota hai ki aapka hosting server YouTube ko block kar raha hai, code nahi!)*"
        )
        
    if not stream_url:
        return await status.edit_text("❌ **Sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ!**")
    
    if chat_id not in music_queue:
        music_queue[chat_id] = []

    try:
        if chat_id in playing_now:
            music_queue[chat_id].append({"title": title, "url": stream_url, "thumb": thumb, "duration": duration})
            return await status.edit_text(f"✅ **Aᴅᴅᴇᴅ ᴛᴏ Qᴜᴇᴜᴇ:** `{title}`")
            
        playing_now.append(chat_id)
        await call_py.play(chat_id, MediaStream(stream_url))
        
        await status.delete()
        await message.reply_photo(
            photo=thumb,
            caption=(f"🎶 **Nᴏᴡ Pʟᴀʏɪɴɢ:** `{title}`\n\n⏳ `00:00 ━━━━●─────── {duration}`\n"
                     f"🔊 **Vᴏʟᴜᴍᴇ:** 100% 🟢\n🎧 **Rᴇǫᴜᴇsᴛᴇᴅ ʙʏ:** {message.from_user.mention}"),
            reply_markup=play_markup()
        )
    except Exception as e:
        if chat_id in playing_now: playing_now.remove(chat_id)
        await status.edit_text(f"❌ **VC Eʀʀᴏʀ:** `{e}`")

# 3. Queue Tracker System
@call_py.on_update(ptc_filters.stream_end)
async def stream_end_handler(client: PyTgCalls, update):
    chat_id = update.chat_id
    if chat_id in music_queue and len(music_queue[chat_id]) > 0:
        next_track = music_queue[chat_id].pop(0)
        await client.play(chat_id, MediaStream(next_track["url"]))
        await app.send_photo(
            chat_id,
            photo=next_track["thumb"],
            caption=f"🎶 **Nᴏᴡ Pʟᴀʏɪɴɢ ғʀᴏᴍ Qᴜᴇᴜᴇ:** `{next_track['title']}`\n⏳ `00:00 ━━━━●─────── {next_track['duration']}`",
            reply_markup=play_markup()
        )
    else:
        if chat_id in playing_now: playing_now.remove(chat_id)
        await client.leave_call(chat_id)
        await app.send_message(chat_id, "🛑 **Qᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ. Lᴇᴀᴠɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.**")

# 4. Commands (Skip, Stop, Pause, Resume)
@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client, message):
    chat_id = message.chat.id
    if chat_id in music_queue and len(music_queue[chat_id]) > 0:
        next_track = music_queue[chat_id].pop(0)
        await call_py.play(chat_id, MediaStream(next_track["url"]))
        await message.reply_text(f"⏭ **Sᴋɪᴘᴘᴇᴅ! Nᴏᴡ Pʟᴀʏɪɴɢ:** `{next_track['title']}`")
    else:
        if chat_id in playing_now: playing_now.remove(chat_id)
        await call_py.leave_call(chat_id)
        await message.reply_text("🛑 **Nᴏ ᴍᴏʀᴇ sᴏɴɢs ɪɴ ǫᴜᴇᴜᴇ. Lᴇᴀᴠɪɴɢ VC.**")

@app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client, message):
    chat_id = message.chat.id
    if chat_id in playing_now: playing_now.remove(chat_id)
    if chat_id in music_queue: music_queue[chat_id].clear()
    try:
        await call_py.leave_call(chat_id)
        await message.reply_text("🛑 **Mᴜsɪᴄ sᴛᴏᴘᴘᴇᴅ ᴀɴᴅ ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ.**")
    except:
        pass

@app.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply_text("⏸ **Sᴛʀᴇᴀᴍ Pᴀᴜsᴇᴅ!**")
    except:
        pass

@app.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply_text("▶️ **Sᴛʀᴇᴀᴍ Rᴇsᴜᴍᴇᴅ!**")
    except:
        pass

# 5. Inline Buttons Callback Handler
@app.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    chat_id = query.message.chat.id
    
    if data == "pause":
        try:
            await call_py.pause_stream(chat_id)
            await query.answer("Stream Paused ⏸", show_alert=True)
        except:
            await query.answer("Already paused!", show_alert=True)
            
    elif data == "resume":
        try:
            await call_py.resume_stream(chat_id)
            await query.answer("Stream Resumed ▶️", show_alert=True)
        except:
            await query.answer("Already playing!", show_alert=True)
            
    elif data == "stop":
        if chat_id in playing_now: playing_now.remove(chat_id)
        if chat_id in music_queue: music_queue[chat_id].clear()
        try:
            await call_py.leave_call(chat_id)
            await query.message.delete()
        except:
            pass

    elif data == "skip":
        if chat_id in music_queue and len(music_queue[chat_id]) > 0:
            next_track = music_queue[chat_id].pop(0)
            await call_py.play(chat_id, MediaStream(next_track["url"]))
            await query.message.delete()
            await app.send_photo(
                chat_id, photo=next_track["thumb"],
                caption=f"🎶 **Nᴏᴡ Pʟᴀʏɪɴɢ:** `{next_track['title']}`",
                reply_markup=play_markup()
            )
        else:
            if chat_id in playing_now: playing_now.remove(chat_id)
            await call_py.leave_call(chat_id)
            await query.message.delete()

# ----------------- DUMMY WEB SERVER -----------------
web_app = Flask(__name__)
@web_app.route('/')
def home():
    return "⚡️ KSHATRIYA OP Music Bot is Alive! ⚡️"
def run_web():
    web_app.run(host="0.0.0.0", port=random.randint(2000, 9000))

# ----------------- STARTUP -----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    app.start()
    call_py.start()
    print("KSHATRIYA OP Music Bot is ACTIVE! ⚡️")
    idle()
