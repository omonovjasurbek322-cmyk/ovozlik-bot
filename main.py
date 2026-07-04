import os
from db import init_db
from bot import run_bot

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        print("Set it with: $env:TELEGRAM_BOT_TOKEN = 'your_token_here'")
        exit(1)

    init_db()
    run_bot(TOKEN)
