# Telegram Bot Token (обязательно)
BOT_TOKEN=

# Kinopoisk API Key (обязательно)
KINOPOISK_API_KEY=

# База данных (сейчас используется PostgreSQL)
DATABASE_URL=sqlite+aiosqlite:///./watchlist.db
DATABASE_URL=postgresql+asyncpg://user:password@localhost:/

# Redis (раскомментируйте, если Redis запущен)
REDIS_URL=redis://localhost:6379/0

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Пороги голосования
VOTE_THRESHOLD=2
MIN_VOTERS=2

# Ограничение доступа (укажите свои ID)
ALLOWED_USER_IDS=
ALLOWED_CHAT_IDS=