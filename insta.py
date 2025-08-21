import json
import os
import time
import random
from datetime import datetime
from instagrapi import Client

SESSION_FILE = "session.json"
REPLIED_FILE = "replied_users.json"
RESET_HOUR = 0  # reset at midnight

USERNAME = "hixolo4923"
PASSWORD = "AAA@@@333.com"

# ---------------------------
# JSON Helpers
# ---------------------------
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------
# Daily Reset
# ---------------------------
def reset_if_needed(replied_users):
    now = datetime.now()
    last_reset = replied_users.get("_last_reset")
    today = now.strftime("%Y-%m-%d")

    if last_reset != today and now.hour >= RESET_HOUR:
        replied_users = {"_last_reset": today}
        save_json(REPLIED_FILE, replied_users)
        print("🔄 Reset replied_users for new day")
    return replied_users

# ---------------------------
# Login & Session
# ---------------------------
def login():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)
    try:
        cl.login(USERNAME, PASSWORD)
    except Exception:
        cl.set_settings({})
        cl.login(USERNAME, PASSWORD)
    cl.dump_settings(SESSION_FILE)
    return cl

# ---------------------------
# Intent Detection
# ---------------------------
def get_intent(text):
    text = text.lower().strip()
    if text in ["hello", "hey", "hi", "bonjour"]:
        return "hello"
    elif text in ["1", "rendez", "rendez-vous"]:
        return "rendez-vous"
    elif text in ["2", "service", "services"]:
        return "service"
    return None

def reply_for_intent(intent):
    if intent == "hello":
        return ("👋 Bonjour, voici notre menu :\n"
                "1️⃣ Pour prendre un rendez-vous envoyez *1*\n"
                "2️⃣ Pour nos services envoyez *2*")
    elif intent == "rendez-vous":
        return "📅 Pour prendre un rendez-vous, contactez ce numéro : +213XXXXXXXXX"
    elif intent == "service":
        return "💼 Nos services :\n- Détartrage\n- Blanchiment\n- Consultation"
    return None

# ---------------------------
# Process Threads
# ---------------------------
def process_threads(cl, replied_users, mode="inbox"):
    if mode == "pending":
        # Pending = unread messages (non-followers usually)
        threads = cl.direct_threads(selected_filter="unread", amount=10)
    else:
        threads = cl.direct_threads(amount=10)

    for thread in threads:
        if not thread.messages:
            continue

        message = thread.messages[0]
        user_id = str(message.user_id)
        text = message.text or ""

        intent = get_intent(text)
        if not intent:
            continue

        if user_id not in replied_users:
            replied_users[user_id] = []

        if intent in replied_users[user_id]:
            continue

        reply_text = reply_for_intent(intent)
        if reply_text:
            time.sleep(random.uniform(2, 5))  # anti-spam delay
            cl.direct_send(reply_text, [user_id])
            print(f"✅ Replied to {user_id} with intent '{intent}'")

            replied_users[user_id].append(intent)
            save_json(REPLIED_FILE, replied_users)

# ---------------------------
# Main Loop
# ---------------------------
def auto_reply(cl):
    replied_users = load_json(REPLIED_FILE, {"_last_reset": datetime.now().strftime("%Y-%m-%d")})
    while True:
        replied_users = reset_if_needed(replied_users)
        process_threads(cl, replied_users, mode="inbox")    # normal inbox
        process_threads(cl, replied_users, mode="pending")  # unread/pending
        time.sleep(10)

# ---------------------------
# Run Bot
# ---------------------------
if __name__ == "__main__":
    cl = login()
    auto_reply(cl)
