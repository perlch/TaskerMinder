#the based language for this bot was RU so im sorry
import telebot
from telebot import types
import re
import os
import time
from datetime import datetime
from threading import Thread

TOKEN = "TOKEN_GOES_HERE"
bot = telebot.TeleBot(TOKEN)

REM_FILE = "userdatatime.txt"
PLANS_FILE = "usertasks.txt"

for f in [REM_FILE, PLANS_FILE]:
    if not os.path.exists(f):
        with open(f, 'w', encoding='utf-8') as file: pass

if not hasattr(bot, 'temp_tasks'):
    bot.temp_tasks = {}

def main_kb():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Напоминалка ⏰", callback_data="go_rem"))
    markup.add(types.InlineKeyboardButton("Планы 📝", callback_data="go_plans"))
    return markup

def rem_menu_kb(done=False):
    markup = types.InlineKeyboardMarkup()
    t = "Что запоминаем? ✅" if done else "Что запоминаем?"
    markup.add(types.InlineKeyboardButton(t, callback_data="set_task"))
    markup.add(types.InlineKeyboardButton("Когда напоминаем?", callback_data="set_time"))
    markup.add(types.InlineKeyboardButton("Мои напоминания 📋", callback_data="list_rems"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return markup

def list_rems_kb(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="go_rem"))
    if os.path.exists(REM_FILE):
        with open(REM_FILE, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                parts = line.strip().split(" : ")
                if len(parts) == 3 and parts[0] == str(user_id):
                    markup.add(types.InlineKeyboardButton(f"❌ {parts[2]} - {parts[1]}", callback_data=f"delrem_{i}"))
    return markup

def plans_kb(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Покинуть планы", callback_data="back"))
    plans = []
    if os.path.exists(PLANS_FILE):
        with open(PLANS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(f"{user_id} :"):
                    plans = line.strip().split(" : ")[1:]
                    break
    for p in plans:
        markup.add(types.InlineKeyboardButton(f"❌ {p}", callback_data=f"delplan_{p}"))
    label = "Добавить план" if plans else "Создать план"
    markup.add(types.InlineKeyboardButton(label, callback_data="add_p"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Что запомним, когда напомним?", reply_markup=main_kb())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.from_user.id
    if call.data == "back":
        bot.edit_message_text("Что запомним, когда напомним?", call.message.chat.id, call.message.message_id, reply_markup=main_kb())
    elif call.data == "go_rem":
        bot.edit_message_text("Настройка напоминаний:", call.message.chat.id, call.message.message_id, reply_markup=rem_menu_kb())
    elif call.data == "list_rems":
        bot.edit_message_text("Ваши напоминания (нажмите для удаления):", call.message.chat.id, call.message.message_id, reply_markup=list_rems_kb(uid))
    elif call.data.startswith("delrem_"):
        idx = int(call.data.split("_")[1])
        lines = []
        with open(REM_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
        with open(REM_FILE, 'w', encoding='utf-8') as f:
            for i, line in enumerate(lines):
                if i != idx: f.write(line)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=list_rems_kb(uid))
    elif call.data == "set_task":
        msg = bot.send_message(call.message.chat.id, "Введите задачу, которую я тебе напомню:")
        bot.register_next_step_handler(msg, save_task_text, call.message.message_id)
    elif call.data == "set_time":
        msg = bot.send_message(call.message.chat.id, "Запишите время (например 14:30 или 4:30):")
        bot.register_next_step_handler(msg, save_time, call.message.message_id)
    elif call.data == "go_plans":
        bot.edit_message_text("Ваш лист планов:", call.message.chat.id, call.message.message_id, reply_markup=plans_kb(uid))
    elif call.data == "add_p":
        msg = bot.send_message(call.message.chat.id, "Напишите план:")
        bot.register_next_step_handler(msg, save_plan, call.message.message_id)
    elif call.data.startswith("delplan_"):
        val = call.data.replace("delplan_", "")
        lines = []
        with open(PLANS_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
        with open(PLANS_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith(f"{uid} :"):
                    parts = line.strip().split(" : ")
                    new_parts = [p for p in parts if p != val]
                    if len(new_parts) > 1: f.write(" : ".join(new_parts) + "\n")
                else: f.write(line)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=plans_kb(uid))

def save_task_text(message, menu_id):
    bot.temp_tasks[message.from_user.id] = message.text
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, message.message_id - 1)
    except: pass
    bot.edit_message_reply_markup(message.chat.id, menu_id, reply_markup=rem_menu_kb(True))

def save_time(message, menu_id):
    if not re.match(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$', message.text):
        msg = bot.send_message(message.chat.id, "Ошибка! Введите время как 4:30 или 14:30:")
        bot.register_next_step_handler(msg, save_time, menu_id)
        return
    user_time = message.text
    if len(user_time) == 4: user_time = "0" + user_time
    task = bot.temp_tasks.get(message.from_user.id, "Без названия")
    with open(REM_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{message.from_user.id} : {task} : {user_time}\n")
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, message.message_id - 1)
        bot.delete_message(message.chat.id, menu_id)
    except: pass
    bot.send_message(message.chat.id, f"✅ Напомню в {user_time}: {task}")

def save_plan(message, menu_id):
    uid = str(message.from_user.id)
    new_plan = message.text.replace(":", "")
    lines = []
    found = False
    if os.path.exists(PLANS_FILE):
        with open(PLANS_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
    with open(PLANS_FILE, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith(f"{uid} :"):
                f.write(line.strip() + f" : {new_plan}\n")
                found = True
            else: f.write(line)
        if not found: f.write(f"{uid} : {new_plan}\n")
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, message.message_id - 1)
    except: pass
    bot.edit_message_reply_markup(message.chat.id, menu_id, reply_markup=plans_kb(uid))

def checker():
    while True:
        now = datetime.now().strftime("%H:%M")
        if os.path.exists(REM_FILE):
            with open(REM_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
            stay = []
            changed = False
            for line in lines:
                parts = line.strip().split(" : ")
                if len(parts) == 3:
                    if parts[2] == now:
                        try: 
                            bot.send_message(parts[0], f"⏰ НАПОМИНАНИЕ:\n{parts[1]}")
                            changed = True
                        except: stay.append(line)
                    else: stay.append(line)
                else: stay.append(line)
            if changed:
                with open(REM_FILE, 'w', encoding='utf-8') as f: f.writelines(stay)
        time.sleep(60)

if __name__ == "__main__":
    Thread(target=checker, daemon=True).start()
    bot.infinity_polling()
                   
