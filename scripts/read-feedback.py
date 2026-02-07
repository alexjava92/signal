#!/usr/bin/env python3
"""
Read all feedback at the start of a session.
Sources: Telegram bot messages, Telegram channel reactions, GitHub Discussions.
Run this first thing when waking up.

Reads tokens from ../.env file.
Saves reactions to ../data/reactions.json so they persist between sessions.
"""
import os
import json
import requests
from datetime import datetime

# Load .env
env = {}
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()

TG_TOKEN = env.get('TG_TOKEN', '')
GH_TOKEN = env.get('GH_TOKEN', '')

# Persistent storage for reactions
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
REACTIONS_FILE = os.path.join(DATA_DIR, 'reactions.json')
OFFSET_FILE = os.path.join(DATA_DIR, 'tg_offset.txt')

os.makedirs(DATA_DIR, exist_ok=True)


def load_reactions():
    if os.path.exists(REACTIONS_FILE):
        with open(REACTIONS_FILE) as f:
            return json.load(f)
    return {}


def save_reactions(reactions):
    with open(REACTIONS_FILE, 'w') as f:
        json.dump(reactions, f, ensure_ascii=False, indent=2)


def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            return int(f.read().strip())
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, 'w') as f:
        f.write(str(offset))


def read_telegram():
    """Read messages and reactions from Telegram."""
    print("=" * 50)
    print("TELEGRAM FEEDBACK")
    print("=" * 50)

    if not TG_TOKEN:
        print("(TG_TOKEN not set)")
        return

    API = f"https://api.telegram.org/bot{TG_TOKEN}"
    offset = load_offset()

    # Request all update types including reactions
    params = {"timeout": 0}
    if offset:
        params["offset"] = offset

    r = requests.post(f"{API}/getUpdates", json={
        "allowed_updates": [
            "message", "channel_post",
            "message_reaction", "message_reaction_count"
        ],
        **params
    })
    data = r.json()

    if not data.get("ok"):
        print("(ошибка API)")
        return

    updates = data.get("result", [])
    reactions = load_reactions()
    messages = []
    new_reactions = []
    max_offset = offset

    for u in updates:
        uid = u["update_id"]
        if uid >= max_offset:
            max_offset = uid + 1

        # Text messages to the bot (feedback)
        if "message" in u:
            msg = u["message"]
            user = msg.get("from", {})
            text = msg.get("text", "")
            date = datetime.fromtimestamp(msg.get("date", 0))
            name = user.get("first_name", "") + " " + user.get("last_name", "")
            messages.append((date, name.strip(), user.get("username", "?"), text))

        # Channel reactions (anonymous counts)
        if "message_reaction_count" in u:
            mrc = u["message_reaction_count"]
            msg_id = str(mrc.get("message_id", ""))
            date = datetime.fromtimestamp(mrc.get("date", 0))
            for react in mrc.get("reactions", []):
                rtype = react.get("type", {})
                emoji = rtype.get("emoji", rtype.get("custom_emoji_id", "?"))
                count = react.get("total_count", 0)
                # Save to persistent storage
                if msg_id not in reactions:
                    reactions[msg_id] = {}
                reactions[msg_id][emoji] = count
                new_reactions.append((msg_id, emoji, count, date))

        # Individual reactions (non-anonymous chats)
        if "message_reaction" in u:
            mr = u["message_reaction"]
            msg_id = str(mr.get("message_id", ""))
            user = mr.get("user", {})
            new_r = mr.get("new_reaction", [])
            for react in new_r:
                emoji = react.get("emoji", "?")
                name = user.get("first_name", "")
                new_reactions.append((msg_id, emoji, name, None))

    # Save offset and reactions
    if max_offset > offset:
        save_offset(max_offset)
    if new_reactions:
        save_reactions(reactions)

    # Print messages
    if messages:
        print("\nСообщения:")
        for date, name, username, text in messages:
            print(f"  [{date}] {name} (@{username}): {text}")
    else:
        print("(нет новых сообщений)")

    # Print new reactions from this fetch
    if new_reactions:
        print(f"\nНовые реакции:")
        for msg_id, emoji, count_or_name, date in new_reactions:
            if date:
                print(f"  сообщение #{msg_id}: {emoji} x{count_or_name}")
            else:
                print(f"  сообщение #{msg_id}: {emoji} от {count_or_name}")

    # Print accumulated reactions summary
    if reactions:
        print(f"\nВсе накопленные реакции:")
        for msg_id in sorted(reactions.keys(), key=lambda x: int(x)):
            emojis = reactions[msg_id]
            summary = " ".join(f"{e}x{c}" for e, c in emojis.items())
            print(f"  сообщение #{msg_id}: {summary}")
    else:
        print("\n(нет сохранённых реакций)")

    print()


def read_discussions():
    """Read GitHub Discussions."""
    print("=" * 50)
    print("GITHUB DISCUSSIONS")
    print("=" * 50)

    if not GH_TOKEN:
        print("(GH_TOKEN not set)")
        return

    query = """
    query {
      repository(owner: "alexjava92", name: "signal") {
        discussions(first: 20, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            title
            body
            createdAt
            author { login }
            comments(first: 10) {
              nodes {
                body
                createdAt
                author { login }
              }
            }
          }
        }
      }
    }
    """

    r = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"bearer {GH_TOKEN}"},
        json={"query": query}
    )

    data = r.json()
    discussions = data.get("data", {}).get("repository", {}).get("discussions", {}).get("nodes", [])

    if not discussions:
        print("(нет обсуждений)")
        return

    for d in discussions:
        print(f"\n[{d['createdAt'][:10]}] {d['author']['login']}: {d['title']}")
        if d['body']:
            print(f"  {d['body'][:200]}")
        for c in d.get('comments', {}).get('nodes', []):
            print(f"  └─ [{c['createdAt'][:10]}] {c['author']['login']}: {c['body'][:200]}")

    print()


if __name__ == "__main__":
    print("\nREADING FEEDBACK — signal session start\n")
    read_telegram()
    read_discussions()
    print("=" * 50)
    print("END OF FEEDBACK")
    print("=" * 50)
