#!/usr/bin/env python3
"""
Read all feedback at the start of a session.
Sources: Telegram bot messages, GitHub Discussions.
Run this first thing when waking up.

Reads tokens from ../.env file.
"""
import os
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


def read_telegram():
    """Read messages sent to the bot."""
    print("=" * 50)
    print("TELEGRAM FEEDBACK")
    print("=" * 50)

    if not TG_TOKEN:
        print("(TG_TOKEN not set)")
        return

    r = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates")
    data = r.json()

    if not data.get("ok") or not data.get("result"):
        print("(нет новых сообщений)")
        return

    for update in data["result"]:
        msg = update.get("message", {})
        if not msg:
            continue
        user = msg.get("from", {})
        text = msg.get("text", "")
        date = datetime.fromtimestamp(msg.get("date", 0))
        name = user.get("first_name", "") + " " + user.get("last_name", "")
        print(f"\n[{date}] {name.strip()} (@{user.get('username', '?')}):")
        print(f"  {text}")

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
