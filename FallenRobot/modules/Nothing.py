from datetime import datetime, timedelta
import time
import pytz
import os
from logging import getLogger
from PIL import Image, ImageChops, ImageDraw, ImageFont
import textwrap
from pyrogram import filters, Client
from pyrogram.types import ChatMemberUpdated
from FallenRobot import pbot as app
from FallenRobot.utils.errors import capture_err, asyncify
from FallenRobot.utils.utils import temp

LOGGER = getLogger(__name__)

def circle(pfp, size=(215, 215)):
    pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def draw_multiple_line_text(image, text, font, text_start_height):
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=45)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text), line, font=font, fill="white")
        y_text += line_height

@asyncify
def welcomepic(pic, user, chat, count, id):
    new_count = count + 1

    background = Image.open("assets/bg.png")  # <- Background Image (Should be PNG)
    background = background.resize((1280, 720), Image.ANTIALIAS)
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((355, 355))  # Resizes the Profilepicture so it fits perfectly in the circle
    font = ImageFont.truetype("assets/Calistoga-Regular.ttf", 42)  # <- Text Font of the Member Count. Change the text size for your preference
    member_text = f"NAME: {user}"  # <- Text under the Profilepicture with the Membercount
    draw_multiple_line_text(background, member_text, font, 435)
    draw_multiple_line_text(background, chat, font, 47)
    ImageDraw.Draw(background).text(
        (43, 600),
        f"YOU ARE {new_count}TH MEMBER HERE",
        font=ImageFont.truetype("assets/Calistoga-Regular.ttf", 30),
        size=25,
        align="right",
    )
    background.paste(pfp, (35, 194), pfp)  # Pastes the Profilepicture on the Background Image
    welcome_filename = f"downloads/welcome#{id}.png"
    background.save(welcome_filename)  # Saves the finished Image in the folder with the filename
    return welcome_filename

@app.on_chat_member_updated(filters.group)
@capture_err
async def member_has_joined(_, member: ChatMemberUpdated):
    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return
    
    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    if user.is_bot:
        return  # Ignore bots
    
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    timezone = pytz.timezone("Asia/Kolkata")
    joined_date = datetime.fromtimestamp(time.time(), tz=timezone).strftime("%d %B %Y %I:%M:%S %p")
    first_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    id = user.id
    dc = user.dc_id or "Member tanpa PP"
    count = await app.get_chat_members_count(member.chat.id)
    
    try:
        pic = await app.download_media(user.photo.big_file_id, file_name=f"pp{user.id}.png")
    except AttributeError:
        pic = "assets/profilepic.png"
    
    welcomeimg = await welcomepic(pic, user.first_name, member.chat.title, count, user.id)
    await app.send_photo(
        member.chat.id,
        photo=welcomeimg,
        caption=f"<b>𝙷ᴇʏ✨</b> <b>{mention}</b>, <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ {member.chat.title}!</b>\n\n<b>ɴᴀᴍᴇ:</b> <code>{first_name}</code>\n<b>ɪᴅ:</b> <code>{id}</code>\n<b>ᴅᴀᴛᴇ:</b> <code>{joined_date}</code>",
    )
    
    try:
        os.remove(welcomeimg)
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass
        
