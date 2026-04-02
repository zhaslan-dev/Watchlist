import asyncio
import sys
from Watchlist.logging_config import setup_logging
from Watchlist.infrastructure.bot.main import start_bot

def main() -> None:
    setup_logging()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("Bot stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()