# -*- coding: utf-8 -*-
import telebot
from telebot import types
import json
import os
import threading
import time

TOKEN = "7740743461:AAH56GpJm1okAzl8Sh4RPPRf--LQJ9P8Uy0"
ADMIN_ID = 244039842

# حتماً با VPN اجرا کن (Psiphon, Lantern, v2rayN, هر چی داری)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DB = "shop_db.json"
state = {}

# دیتابیس — این بار بدون هیچ خطا
if os.path.exists(DB):
    try:
        with open(DB, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        os.remove(DB)
        data = {"card":"6037-9911-2233-4455","discount":0,"plans":{"1m":185000,"3m":510000,"6m":990000,"12m":2000000},"users":{},"pending":{}}
else:
    data = {"card":"6037-9911-2233-4455","discount":0,"plans":{"1m":185000,"3m":510000,"6m":990000,"12m":2000000},"users":{},"pending":{}}

def save():
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def u(uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0}
        save()
    return data["users"][uid]

def menu(cid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    prices = [185000, 510000, 990000, 2000000]
    names = ["۱ ماهه", "۳ ماهه", "۶ ماهه", "۱ ساله"]
    for i in range(4):
        p = int(prices[i] * (100 - data["discount"]) / 100)
        kb.add(types.InlineKeyboardButton(f"{names[i]} › {p:,} ت", callback_data=f"buy_{i}"))
    kb.row(types.InlineKeyboardButton("کیف پول", callback_data="wal"))
    kb.row(types.InlineKeyboardButton("شارژ حساب", callback_data="charge"))
    if cid == ADMIN_ID:
        kb.row(types.InlineKeyboardButton("پنل ادمین", callback_data="admin"))
    bot.send_message(cid, "<b>منوی فروشگاه</b>", reply_markup=kb)

@bot.message_handler(commands=["start"])
@bot.message_handler(func=lambda m: True)
def start(m):
    u(m.chat.id)
    menu(m.chat.id)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    prices = [185000, 510000, 990000, 2000000]
    names = ["۱ ماهه", "۳ ماهه", "۶ ماهه", "۱ ساله"]

    if c.data.startswith("buy_"):
        i = int(c.data[4:])
        price = int(prices[i] * (100 - data["discount"]) / 100)
        if u(uid)["balance"] >= price:
            u(uid)["balance"] -= price
            save()
            bot.send_message(uid, f"<b>خرید {names[i]} موفق بود!</b>\nموجودی: <code>{u(uid)['balance']:,}</code> تومان")
            menu(uid)
        else:
            bot.answer_callback_query(c.id, "موجودی کافی نیست!", show_alert=True)

    elif c.data == "wal":
        bot.edit_message_text(f"<b>کیف پول:</b>\n<code>{u(uid)['balance']:,}</code> تومان", c.message.chat.id, c.message.message_id)

    elif c.data == "charge":
        bot.send_message(uid, f"واریز کن و <b>رسید</b> بفرست:\n<code>{data['card']}</code>")
        state[uid] = "wait"

    elif c.data == "admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("تغییر کارت", callback_data="ch_card"))
        bot.edit_message_text("<b>پنل ادمین فعال شد</b>", c.message.chat.id, c.message.message_id, reply_markup=kb)

# رسید کاربر
@bot.message_handler(content_types=['photo', 'document'], func=lambda m: state.get(m.chat.id) == "wait")
def receipt(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("تأیید", callback_data=f"ok_{m.chat.id}"))
    kb.add(types.InlineKeyboardButton("رد", callback_data=f"no_{m.chat.id}"))
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(ADMIN_ID, f"رسید جدید از کاربر {m.chat.id}", reply_markup=kb)
    bot.reply_to(m, "رسید ارسال شد، منتظر تأیید ادمین...")
    state.pop(m.chat.id, None)

# تأیید و رد ادمین
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def admin_act(c):
    if c.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(c.id)
    uid = int(c.data.split("_")[1])
    if c.data.startswith("ok_"):
        bot.send_message(ADMIN_ID, f"مبلغ برای کاربر {uid} رو بنویس:")
        state[ADMIN_ID] = f"add_{uid}"
    else:
        bot.send_message(uid, "رسید شما رد شد")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and state.get(m.chat.id, "").startswith("add_"))
def add_money(m):
    try:
        amount = int(m.text.replace(",", ""))
        uid = int(state[m.chat.id].split("_")[1])
        u(uid)["balance"] += amount
        save()
        bot.send_message(uid, f"حساب شما {amount:,} تومان شارژ شد!")
        bot.reply_to(m, "موفق بود")
        state.pop(ADMIN_ID, None)
    except:
        bot.reply_to(m, "فقط عدد بنویس!")

# ذخیره خودکار
threading.Thread(target=lambda: [time.sleep(30), save()], daemon=True).start()

print("ربات آماده است — فقط با VPN اجرا کن!")
bot.infinity_polling(none_stop=True, interval=0)