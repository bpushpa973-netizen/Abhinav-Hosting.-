#!/usr/bin/env python3
"""
🎯 Welcome Bot — by @NIROB353
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot group এ add হলেই group নাম দিয়ে auto welcome + auto link ban
✅ Admin/Owner link দিলে কিছুই হবে না — শুধু normal user এর link delete
✅ /mute — Rose Bot style (reply + time → "Click to Admin Approve" button)
✅ /unmute — reply করে mute তুলবে, Telegram restrict ও তুলবে
✅ /mute শুধু group এ কাজ করবে, DM তে না
✅ সাধারণ user /mute দিলে বলবে "This command is for admins only"
✅ Admin অন্য admin কে mute করতে পারবে না
✅ /setwelcome — group নাম দিয়ে welcome reset (admin only)
✅ /customwelcome — custom welcome set (admin only)
✅ /banwelcome — custom সরিয়ে default চালু (admin only)
✅ বাংলা/English toggle → সব message ভাষা বদলায় (menu সহ)
✅ /start DM এ Rose Bot style menu (সব command দেখায়)
✅ /id — নিজের + group এর chat ID
✅ Group এ /start দিয়ে ভাষা বদলানো → শুধু admin পারবে
✅ "FF TCP FILE UPDATES" নয়, "Welcome Bot" দেখাবে DM এ
✅ Welcome message এ group এর real নাম বসবে
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pip install pyTelegramBotAPI
python welcome-bot.py
"""

import re
import time
import telebot
from telebot.types import (
    Message, ChatMemberUpdated,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ChatPermissions
)

# ─── CONFIG ──────────────────────────────────────────────────────────────
BOT_TOKEN  = "8633637362:AAFuEzZL6nn5NXo1BGlC3NqgG74AJVeiOtM"
OWNER      = "@NIROB353"
GROUP_LINK = "https://t.me/ffallfileupdate"
# ─────────────────────────────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# { str(chat_id): {"group_name":str, "custom":str|None, "lang":"bn"|"en"} }
group_settings = {}
# { str(user_id): "bn"|"en" }
user_language  = {}
# { str(chat_id): { str(user_id): unmute_unix_timestamp } }
muted_users    = {}

URL_PATTERN = re.compile(
    r"(https?://|t\.me/|@\w{5,}|telegram\.me/|telegram\.dog/)",
    re.IGNORECASE
)


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def gs(chat_id):
    k = str(chat_id)
    if k not in group_settings:
        group_settings[k] = {"group_name": "Group", "custom": None, "lang": "bn"}
    return group_settings[k]

def get_user_lang(user_id):
    return user_language.get(str(user_id), "bn")

def set_user_lang(user_id, lang):
    user_language[str(user_id)] = lang

def is_admin(chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except Exception:
        return False

def is_group(chat_type):
    return chat_type in ("group", "supergroup")

def live_group_name(chat_id):
    try:
        return bot.get_chat(chat_id).title or "Group"
    except Exception:
        return "Group"

def parse_dur(s):
    s = s.strip().lower()
    if s.endswith('d'):   return int(s[:-1]) * 86400
    elif s.endswith('h'): return int(s[:-1]) * 3600
    elif s.endswith('m'): return int(s[:-1]) * 60
    elif s.endswith('s'): return int(s[:-1])
    else:                 return int(s) * 60

def fmt_dur(sec):
    if sec >= 86400:  return f"{sec//86400} day(s)"
    elif sec >= 3600: return f"{sec//3600} hour(s)"
    elif sec >= 60:   return f"{sec//60} minute(s)"
    else:             return f"{sec} second(s)"

def is_muted(chat_id, user_id):
    k = str(chat_id); u = str(user_id)
    if k in muted_users and u in muted_users[k]:
        if time.time() < muted_users[k][u]:
            return True
        del muted_users[k][u]
    return False

def do_mute(chat_id, user_id, seconds):
    k = str(chat_id); u = str(user_id)
    until = int(time.time() + seconds)
    muted_users.setdefault(k, {})[u] = until
    try:
        bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
    except Exception:
        pass

def do_unmute(chat_id, user_id):
    k = str(chat_id); u = str(user_id)
    if k in muted_users and u in muted_users[k]:
        del muted_users[k][u]
    try:
        bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
#  WELCOME MESSAGE BUILDER
# ══════════════════════════════════════════════════════════════════════

def build_welcome(lang, mention, group_name, count):
    if lang == "en":
        return (
            f"🎊✨ <b>WELCOME!</b> ✨🎊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Hello {mention}!\n\n"
            f"🏆 Welcome to <b>{group_name}</b>!\n"
            f"    We're so happy to have you here! 💖\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌟 You are member number <b>{count}</b>! 🎉\n\n"
            f"📌 <b>Group Rules & Guidelines:</b>\n"
            f"   ✅ Be respectful to every member\n"
            f"   ✅ Stay on-topic, no off-topic spam\n"
            f"   ✅ No links or promotions without permission\n"
            f"   ✅ No abusive or offensive language\n"
            f"   ✅ Follow all admin instructions\n"
            f"   ✅ Help and support fellow members\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 Enjoy your stay in <b>{group_name}</b>! 🥳\n"
            f"💬 Feel free to introduce yourself!\n\n"
            f"🤖 Bot by {OWNER}"
        )
    else:
        return (
            f"🎊✨ <b>স্বাগতম!</b> ✨🎊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 হ্যালো {mention}!\n\n"
            f"🏆 <b>{group_name}</b> গ্রুপে\n"
            f"    আপনাকে আন্তরিকভাবে স্বাগত জানাই! 💖\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌟 আপনি এই গ্রুপের <b>{count}</b> তম সদস্য! 🎉\n\n"
            f"📌 <b>গ্রুপের নিয়মাবলী ও নির্দেশনা:</b>\n"
            f"   ✅ সকল সদস্যের সাথে সম্মানজনক আচরণ করুন\n"
            f"   ✅ আলোচনা সবসময় মূল বিষয়ের মধ্যে রাখুন\n"
            f"   ✅ অনুমতি ছাড়া কোনো লিংক বা প্রমোশন নিষিদ্ধ\n"
            f"   ✅ অশ্লীল বা আপত্তিজনক ভাষা ব্যবহার করবেন না\n"
            f"   ✅ অ্যাডমিনদের সকল নির্দেশনা মেনে চলুন\n"
            f"   ✅ অন্যদের সাহায্য করার চেষ্টা করুন\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 <b>{group_name}</b> গ্রুপে আপনাকে পেয়ে\n"
            f"    আমরা অনেক আনন্দিত! 🥳\n"
            f"💬 নিজেকে পরিচয় করিয়ে দিতে পারেন!\n\n"
            f"🤖 Bot by {OWNER}"
        )


# ══════════════════════════════════════════════════════════════════════
#  DM /start MENU — Rose Bot style
# ══════════════════════════════════════════════════════════════════════

def make_main_menu(lang, bu):
    m = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        m.add(
            InlineKeyboardButton("👥 Group",    url=GROUP_LINK),
            InlineKeyboardButton("📤 Share",    switch_inline_query=f"Check this bot! @{bu}")
        )
        m.add(
            InlineKeyboardButton("🇧🇩 বাংলা",  callback_data="lang_bn"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        )
        m.add(InlineKeyboardButton("📋 Commands", callback_data="show_commands"))
        m.add(InlineKeyboardButton("➕ Add me to your Group", url=f"https://t.me/{bu}?startgroup=true"))
    else:
        m.add(
            InlineKeyboardButton("👥 গ্রুপ",    url=GROUP_LINK),
            InlineKeyboardButton("📤 শেয়ার",   switch_inline_query=f"এই বটটি দেখুন! @{bu}")
        )
        m.add(
            InlineKeyboardButton("🇧🇩 বাংলা",  callback_data="lang_bn"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        )
        m.add(InlineKeyboardButton("📋 কমান্ড", callback_data="show_commands"))
        m.add(InlineKeyboardButton("➕ গ্রুপে Add করুন", url=f"https://t.me/{bu}?startgroup=true"))
    return m

def start_text(lang, name):
    if lang == "en":
        return (
            f"╔══════════════════════════╗\n"
            f"       🎯 <b>Welcome Bot</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"😊 Hello <b>{name}</b>! 👋\n"
            f"😉 You're talking to <b>Welcome Bot</b>!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💖 Choose an option below:\n\n"
            f"👥 <b>Group</b>    — Join our official group\n"
            f"📤 <b>Share</b>    — Share bot with friends\n"
            f"🌐 <b>Language</b> — Switch বাংলা/English\n"
            f"📋 <b>Commands</b> — See all bot commands\n"
            f"➕ <b>Add</b>      — Add bot to your group\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Owner: {OWNER}"
        )
    else:
        return (
            f"╔══════════════════════════╗\n"
            f"       🎯 <b>Welcome Bot</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"😊 হ্যালো <b>{name}</b>! 👋\n"
            f"😉 আপনি কথা বলছেন <b>Welcome Bot</b> এর সাথে!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💖 নিচের অপশন বেছে নিন:\n\n"
            f"👥 <b>গ্রুপ</b>    — অফিসিয়াল গ্রুপে যোগ দিন\n"
            f"📤 <b>শেয়ার</b>   — বন্ধুদের সাথে শেয়ার করুন\n"
            f"🌐 <b>ভাষা</b>    — বাংলা/English বেছে নিন\n"
            f"📋 <b>কমান্ড</b>  — সব কমান্ড দেখুন\n"
            f"➕ <b>Add</b>     — গ্রুপে বট Add করুন\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Owner: {OWNER}"
        )

def commands_text(lang):
    if lang == "en":
        return (
            f"╔══════════════════════════╗\n"
            f"       📋 <b>Bot Commands</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"👑 <b>Admin Commands (Group only):</b>\n\n"
            f"🔹 /setwelcome\n"
            f"    Reset welcome using group name\n\n"
            f"🔹 /customwelcome &lt;text&gt;\n"
            f"    Set custom welcome message\n"
            f"    Use <code>{{name}}</code> for member's name\n\n"
            f"🔹 /banwelcome\n"
            f"    Remove custom → use default welcome\n\n"
            f"🔹 /mute 10m  (reply to message)\n"
            f"    Mute a user for set duration\n"
            f"    Formats: <code>30s</code> <code>10m</code> <code>2h</code> <code>1d</code>\n\n"
            f"🔹 /unmute  (reply to message)\n"
            f"    Remove mute from a user\n\n"
            f"🔹 /id\n"
            f"    Show your Chat ID + Group ID\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Auto Features:</b>\n"
            f"• Links auto-deleted for non-admins\n"
            f"• Admins can always send links ✅\n"
            f"• Welcome auto-set when bot is added\n\n"
            f"🤖 Bot by {OWNER}"
        )
    else:
        return (
            f"╔══════════════════════════╗\n"
            f"       📋 <b>বট কমান্ড</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"👑 <b>অ্যাডমিন কমান্ড (শুধু গ্রুপে):</b>\n\n"
            f"🔹 /setwelcome\n"
            f"    গ্রুপের নাম দিয়ে welcome reset করুন\n\n"
            f"🔹 /customwelcome &lt;text&gt;\n"
            f"    নিজের welcome message সেট করুন\n"
            f"    <code>{{name}}</code> লিখলে সদস্যের নাম বসবে\n\n"
            f"🔹 /banwelcome\n"
            f"    Custom সরিয়ে default welcome চালু করুন\n\n"
            f"🔹 /mute 10m  (message reply করে)\n"
            f"    নির্দিষ্ট সময়ের জন্য user মিউট করুন\n"
            f"    Format: <code>30s</code> <code>10m</code> <code>2h</code> <code>1d</code>\n\n"
            f"🔹 /unmute  (message reply করে)\n"
            f"    User এর মিউট তুলে দিন\n\n"
            f"🔹 /id\n"
            f"    আপনার Chat ID + Group ID দেখুন\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>অটো ফিচার:</b>\n"
            f"• Non-admin দের link auto-delete হবে\n"
            f"• Admin সবসময় link দিতে পারবেন ✅\n"
            f"• Bot add হলেই auto welcome সেট হবে\n\n"
            f"🤖 Bot by {OWNER}"
        )

def back_btn(lang):
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton(
        "⬅️ Back" if lang == "en" else "⬅️ ফিরে যান",
        callback_data="back_main"
    ))
    return m


# ══════════════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    cid  = msg.chat.id
    uid  = msg.from_user.id
    name = ((msg.from_user.first_name or "") + " " + (msg.from_user.last_name or "")).strip() or "Friend"

    try:
        bu = bot.get_me().username
    except Exception:
        bu = "WelcomeBot"

    # ── DM → full Rose Bot style menu ────────────────────────────────
    if msg.chat.type == "private":
        lang = get_user_lang(uid)
        bot.send_message(cid, start_text(lang, name), reply_markup=make_main_menu(lang, bu))

    # ── Group → language switch (admin only) ─────────────────────────
    else:
        if not is_admin(cid, uid):
            return   # সাধারণ user → চুপ থাকবে
        lang = gs(cid).get("lang", "bn")
        m = InlineKeyboardMarkup(row_width=2)
        m.add(
            InlineKeyboardButton("🇧🇩 বাংলা",  callback_data=f"glang_bn_{cid}"),
            InlineKeyboardButton("🇬🇧 English", callback_data=f"glang_en_{cid}")
        )
        txt = (f"🌐 <b>Language Settings</b>\n\nCurrent: <b>{'English' if lang=='en' else 'বাংলা'}</b>\n\nSelect group language:"
               if lang == "en" else
               f"🌐 <b>ভাষা সেটিং</b>\n\nবর্তমান: <b>{'English' if lang=='en' else 'বাংলা'}</b>\n\nগ্রুপের ভাষা বেছে নিন:")
        bot.send_message(cid, txt, reply_markup=m)


# ══════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def cb_handler(call):
    uid  = call.from_user.id
    cid  = call.message.chat.id
    data = call.data

    try:
        bu = bot.get_me().username
    except Exception:
        bu = "WelcomeBot"

    # ── DM language switch ────────────────────────────────────────────
    if data in ("lang_bn", "lang_en"):
        new_lang = "bn" if data == "lang_bn" else "en"
        set_user_lang(uid, new_lang)
        alert = "✅ বাংলা নির্বাচন করা হয়েছে!" if new_lang == "bn" else "✅ English selected!"
        bot.answer_callback_query(call.id, alert, show_alert=True)
        name = ((call.from_user.first_name or "") + " " + (call.from_user.last_name or "")).strip() or "Friend"
        try:
            bot.edit_message_text(
                start_text(new_lang, name),
                cid, call.message.message_id,
                reply_markup=make_main_menu(new_lang, bu)
            )
        except Exception:
            pass

    # ── Show commands ─────────────────────────────────────────────────
    elif data == "show_commands":
        lang = get_user_lang(uid)
        try:
            bot.edit_message_text(
                commands_text(lang),
                cid, call.message.message_id,
                reply_markup=back_btn(lang)
            )
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    # ── Back to main ──────────────────────────────────────────────────
    elif data == "back_main":
        lang = get_user_lang(uid)
        name = ((call.from_user.first_name or "") + " " + (call.from_user.last_name or "")).strip() or "Friend"
        try:
            bot.edit_message_text(
                start_text(lang, name),
                cid, call.message.message_id,
                reply_markup=make_main_menu(lang, bu)
            )
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    # ── Group language switch ─────────────────────────────────────────
    elif data.startswith("glang_"):
        parts    = data.split("_")
        new_lang = parts[1]        # "bn" or "en"
        gcid     = int(parts[2])   # group chat_id

        if not is_admin(gcid, uid):
            bot.answer_callback_query(call.id, "❌ Only admins can change group language!", show_alert=True)
            return

        gs(gcid)["lang"] = new_lang
        label = "বাংলা" if new_lang == "bn" else "English"
        bot.answer_callback_query(call.id, f"✅ Group language set to {label}!", show_alert=True)
        try:
            bot.edit_message_text(
                f"✅ <b>Group language set to {label}!</b>\n\nAll bot messages will now be in {label}.",
                cid, call.message.message_id
            )
        except Exception:
            pass

    # ── Mute approve button ───────────────────────────────────────────
    elif data.startswith("mute|"):
        _, gcid_s, tid_s, sec_s, aid_s = data.split("|")
        gcid = int(gcid_s); tid = int(tid_s)
        sec  = int(sec_s);  aid = int(aid_s)

        if uid != aid:
            bot.answer_callback_query(call.id, "❌ Only the admin who requested can approve!", show_alert=True)
            return
        if not is_admin(gcid, uid):
            bot.answer_callback_query(call.id, "❌ You are no longer an admin!", show_alert=True)
            return

        do_mute(gcid, tid, sec)
        dur = fmt_dur(sec)
        try:
            bot.edit_message_text(
                f"🔇 <b>User Muted!</b>\n\n"
                f"👤 User ID: <code>{tid}</code>\n"
                f"⏱ Duration: <b>{dur}</b>\n\n"
                f"✅ Muted successfully.",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
        bot.answer_callback_query(call.id, "✅ User muted!")


# ══════════════════════════════════════════════════════════════════════
#  /id
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["id"])
def cmd_id(msg: Message):
    uid  = msg.from_user.id
    cid  = msg.chat.id
    name = ((msg.from_user.first_name or "") + " " + (msg.from_user.last_name or "")).strip() or "User"
    lang = gs(cid).get("lang", "bn") if is_group(msg.chat.type) else get_user_lang(uid)

    if lang == "en":
        text = (
            f"╔════════════════════╗\n"
            f"       🆔 Chat ID\n"
            f"╚════════════════════╝\n\n"
            f"👤 <b>Name:</b> {name}\n"
            f"🔢 <b>Your ID:</b> <code>{uid}</code>\n"
            f"💬 <b>This Chat ID:</b> <code>{cid}</code>\n\n"
            f"🤖 Bot by {OWNER}"
        )
    else:
        text = (
            f"╔════════════════════╗\n"
            f"       🆔 Chat ID\n"
            f"╚════════════════════╝\n\n"
            f"👤 <b>নাম:</b> {name}\n"
            f"🔢 <b>আপনার ID:</b> <code>{uid}</code>\n"
            f"💬 <b>এই Chat ID:</b> <code>{cid}</code>\n\n"
            f"🤖 Bot by {OWNER}"
        )
    bot.send_message(cid, text)


# ══════════════════════════════════════════════════════════════════════
#  /setwelcome  /customwelcome  /banwelcome  — Admin only, Group only
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["setwelcome"])
def cmd_setwelcome(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id
    if not is_group(msg.chat.type):
        bot.send_message(cid, "⚠️ Only works in groups!" if get_user_lang(uid) == "en" else "⚠️ শুধু গ্রুপে কাজ করে!")
        return
    s = gs(cid); lang = s.get("lang", "bn")
    if not is_admin(cid, uid):
        bot.send_message(cid, "🚫 This command is for <b>admins only</b>!" if lang == "en" else "🚫 এই কমান্ড শুধু <b>অ্যাডমিনদের</b> জন্য!")
        return
    gname = live_group_name(cid)
    s["group_name"] = gname; s["custom"] = None
    bot.send_message(cid,
        f"✅ <b>Welcome set!</b>\n🏆 Group: <b>{gname}</b>\n\nNew members will be welcomed with this group name." if lang == "en"
        else f"✅ <b>Welcome সেট হয়েছে!</b>\n🏆 গ্রুপ: <b>{gname}</b>\n\nনতুন সদস্যরা এই নামে স্বাগত পাবেন।")

@bot.message_handler(commands=["customwelcome"])
def cmd_customwelcome(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id
    if not is_group(msg.chat.type):
        bot.send_message(cid, "⚠️ Only works in groups!" if get_user_lang(uid) == "en" else "⚠️ শুধু গ্রুপে কাজ করে!")
        return
    s = gs(cid); lang = s.get("lang", "bn")
    if not is_admin(cid, uid):
        bot.send_message(cid, "🚫 This command is for <b>admins only</b>!" if lang == "en" else "🚫 এই কমান্ড শুধু <b>অ্যাডমিনদের</b> জন্য!")
        return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(cid,
            "⚠️ Usage: /customwelcome &lt;text&gt;\nUse <code>{name}</code> for member name." if lang == "en"
            else "⚠️ ব্যবহার: /customwelcome &lt;text&gt;\n<code>{name}</code> লিখলে নাম বসবে।")
        return
    s["custom"] = parts[1].strip()
    bot.send_message(cid,
        f"✅ <b>Custom welcome set!</b>\n\n<i>{s['custom']}</i>" if lang == "en"
        else f"✅ <b>Custom welcome সেট হয়েছে!</b>\n\n<i>{s['custom']}</i>")

@bot.message_handler(commands=["banwelcome"])
def cmd_banwelcome(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id
    if not is_group(msg.chat.type):
        bot.send_message(cid, "⚠️ Only works in groups!" if get_user_lang(uid) == "en" else "⚠️ শুধু গ্রুপে কাজ করে!")
        return
    s = gs(cid); lang = s.get("lang", "bn")
    if not is_admin(cid, uid):
        bot.send_message(cid, "🚫 This command is for <b>admins only</b>!" if lang == "en" else "🚫 এই কমান্ড শুধু <b>অ্যাডমিনদের</b> জন্য!")
        return
    s["custom"] = None
    bot.send_message(cid,
        "✅ Custom welcome removed. Default welcome is now active." if lang == "en"
        else "✅ Custom welcome সরানো হয়েছে। Default welcome চালু।")


# ══════════════════════════════════════════════════════════════════════
#  /mute — Rose Bot style (GROUP ONLY)
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["mute"])
def cmd_mute(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id

    # DM এ কাজ করবে না
    if not is_group(msg.chat.type):
        return

    # Admin check — সঠিকভাবে
    if not is_admin(cid, uid):
        bot.send_message(cid,
            "🚫 This command is for <b>admins only</b>!\n"
            "You don't have permission to mute users.")
        return

    # Reply দরকার
    if not msg.reply_to_message:
        bot.send_message(cid,
            "⚠️ <b>Reply to the user's message you want to mute!</b>\n\n"
            "Example: reply to a message → <code>/mute 10m</code>\n\n"
            "Formats: <code>30s</code>  <code>10m</code>  <code>2h</code>  <code>1d</code>")
        return

    target = msg.reply_to_message.from_user
    tid    = target.id

    # Admin কে mute করা যাবে না
    if is_admin(cid, tid):
        bot.send_message(cid,
            f"❌ <b>{target.first_name}</b> is also an admin — cannot be muted!")
        return

    # Time parse
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(cid,
            "⚠️ Provide a time!\n"
            "Example: <code>/mute 10m</code>  <code>/mute 1h</code>  <code>/mute 1d</code>")
        return
    try:
        seconds = parse_dur(parts[1])
    except Exception:
        bot.send_message(cid, "⚠️ Invalid time! Use: <code>30s</code> <code>10m</code> <code>2h</code> <code>1d</code>")
        return

    dur = fmt_dur(seconds)

    # Rose Bot style button
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "✅ Click to Admin Approve",
        callback_data=f"mute|{cid}|{tid}|{seconds}|{uid}"
    ))
    bot.send_message(
        cid,
        f"⚠️ <b>Mute Request</b>\n\n"
        f"👤 User: <a href='tg://user?id={tid}'>{target.first_name}</a>\n"
        f"⏱ Duration: <b>{dur}</b>\n\n"
        f"Admin, please confirm 👇",
        reply_markup=markup
    )


# ══════════════════════════════════════════════════════════════════════
#  /unmute — GROUP ONLY
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["unmute"])
def cmd_unmute(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id

    if not is_group(msg.chat.type):
        return

    if not is_admin(cid, uid):
        bot.send_message(cid,
            "🚫 This command is for <b>admins only</b>!")
        return

    if not msg.reply_to_message:
        bot.send_message(cid, "⚠️ Reply to the user's message you want to unmute!")
        return

    target = msg.reply_to_message.from_user
    result = do_unmute(cid, target.id)
    name   = target.first_name or "User"

    if result:
        bot.send_message(cid,
            f"✅ <b>{name}</b> has been unmuted!\n🔊 They can send messages again.")
    else:
        bot.send_message(cid, f"⚠️ Could not unmute <b>{name}</b> (may need bot admin rights).")


# ══════════════════════════════════════════════════════════════════════
#  MESSAGE FILTER — mute block + link ban (admin EXEMPT)
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(
    func=lambda m: is_group(m.chat.type) and m.text is not None,
    content_types=["text"]
)
def msg_filter(msg: Message):
    cid = msg.chat.id; uid = msg.from_user.id

    # Muted user এর message delete
    if is_muted(cid, uid):
        try:
            bot.delete_message(cid, msg.message_id)
        except Exception:
            pass
        return

    # Admin হলে link check করবে না — সরাসরি return
    if is_admin(cid, uid):
        return

    # Link filter for normal users
    if URL_PATTERN.search(msg.text):
        try:
            bot.delete_message(cid, msg.message_id)
        except Exception:
            pass

        lang    = gs(cid).get("lang", "bn")
        name    = (msg.from_user.first_name or "").strip() or "User"
        mention = f'<a href="tg://user?id={uid}">{name}</a>'

        if lang == "en":
            warn = (
                f"⚠️ <b>Warning!</b>\n\n"
                f"🚫 {mention},\n"
                f"<b>Links are not allowed</b> in this group!\n\n"
                f"Your message has been deleted. ❌\n"
                f"Repeated violations may result in a ban! 🔴\n\n"
                f"🤖 Bot by {OWNER}"
            )
        else:
            warn = (
                f"⚠️ <b>সতর্কবার্তা!</b>\n\n"
                f"🚫 {mention},\n"
                f"এই গ্রুপে <b>লিংক দেওয়া নিষিদ্ধ!</b>\n\n"
                f"আপনার মেসেজ ডিলিট করা হয়েছে। ❌\n"
                f"বারবার নিয়ম ভাঙলে Kick হতে পারেন! 🔴\n\n"
                f"🤖 Bot by {OWNER}"
            )
        bot.send_message(cid, warn)


# ══════════════════════════════════════════════════════════════════════
#  BOT ADDED TO GROUP — auto setup
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(content_types=["new_chat_members"])
def on_bot_added(msg: Message):
    for member in msg.new_chat_members:
        if member.id == bot.get_me().id:
            cid   = msg.chat.id
            gname = live_group_name(cid)
            s     = gs(cid)
            s["group_name"] = gname
            s["custom"]     = None
            s["lang"]       = "bn"
            bot.send_message(
                cid,
                f"👋 <b>আমাকে গ্রুপে যোগ করার জন্য ধন্যবাদ!</b>\n\n"
                f"🏆 গ্রুপ: <b>{gname}</b>\n\n"
                f"✅ <b>Auto welcome</b> — গ্রুপের নামে সেট হয়েছে!\n"
                f"🔒 <b>Link blocking ON</b> — Admin ছাড়া কেউ link দিতে পারবে না\n"
                f"👑 Admin রা সবসময় link দিতে পারবেন\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 <b>Admin কমান্ড:</b>\n"
                f"<code>/setwelcome</code> — Welcome reset\n"
                f"<code>/customwelcome &lt;text&gt;</code> — Custom welcome\n"
                f"<code>/banwelcome</code> — Default welcome\n"
                f"<code>/mute 10m</code> (reply) — User mute\n"
                f"<code>/unmute</code> (reply) — Mute তুলুন\n"
                f"<code>/id</code> — Chat ID দেখুন\n"
                f"<code>/start</code> — ভাষা বদলান\n\n"
                f"🤖 Bot by {OWNER}"
            )


# ══════════════════════════════════════════════════════════════════════
#  NEW MEMBER WELCOME
# ══════════════════════════════════════════════════════════════════════

@bot.chat_member_handler()
def on_member_join(update: ChatMemberUpdated):
    old = update.old_chat_member.status
    new = update.new_chat_member.status
    if old not in ("left", "kicked") or new not in ("member", "administrator", "restricted"):
        return

    user    = update.new_chat_member.user
    cid     = update.chat.id

    # Bot নিজে join করলে skip
    try:
        if user.id == bot.get_me().id:
            gname = live_group_name(cid)
            s = gs(cid)
            s["group_name"] = gname; s["custom"] = None
            return
    except Exception:
        pass

    s      = gs(cid)
    lang   = s.get("lang", "bn")
    gname  = live_group_name(cid)
    s["group_name"] = gname   # always update group name
    custom = s.get("custom")

    first   = user.first_name or ""
    last    = user.last_name  or ""
    name    = (first + " " + last).strip() or ("Member" if lang == "en" else "সদস্য")
    mention = f'<a href="tg://user?id={user.id}">{name}</a>'

    try:
        count = bot.get_chat_member_count(cid)
    except Exception:
        count = "?"

    if custom:
        text = custom.replace("{name}", mention).replace("{group_name}", gname)
    else:
        text = build_welcome(lang, mention, gname, count)

    try:
        bot.send_message(cid, text)
    except Exception as e:
        print(f"[Welcome Error] {e}")


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("🤖  Welcome Bot — STARTED")
    print("✅  Auto link-ban ON  (admins fully exempt)")
    print("✅  Rose Bot /mute with Click to Admin Approve")
    print("✅  /unmute removes Telegram restrict")
    print("✅  Language toggle — all messages change")
    print("✅  DM /start → Rose Bot style menu")
    print(f"👑  Owner: {OWNER}")
    print("=" * 55)
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        allowed_updates=["message", "chat_member", "callback_query"]
    )
