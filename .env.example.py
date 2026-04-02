# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Kinopoisk API Key (получить на https://kinopoiskapiunofficial.tech/)
KINOPOISK_API_KEY=your_api_key_here

# PostgreSQL Database URL (асинхронный формат для asyncpg)
# Формат: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/watchlist

# Redis URL для кэширования
# Формат: redis://host:port/db_number
REDIS_URL=redis://localhost:6379/0

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Настройки голосования
# Разница голосов (За - Против) для принятия фильма
VOTE_THRESHOLD=2
# Минимальное количество проголосовавших для принятия фильма
MIN_VOTERS=2