# Watchlist – Telegram бот для совместной медиа-очереди

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Watchlist – это Telegram бот, который позволяет создавать общую очередь для просмотра фильмов, аниме, спектаклей. Вы можете добавлять медиа через поиск по Кинопоиску, голосовать за/против, просматривать историю принятых фильмов и сразу переходить к поиску на онлайн-кинотеатрах. Бот подходит для пар, групп друзей или семей.

## Возможности

- 🔍 **Поиск фильмов** по названию через Kinopoisk API с пагинацией
- ➕ **Добавление** найденных фильмов в общую очередь
- 👍 **Голосование** «За» или «Против» за каждый элемент очереди
- 📋 **Просмотр текущей очереди** с рейтингами и количеством голосов
- 📜 **История просмотренных** фильмов (команда `/history`)
- 🔗 **Интеграция с онлайн-кинотеатрами** – кнопки для поиска на Кинопоиске, Иви, Okko при принятии фильма
- 🤖 **Инлайн-клавиатуры** и простое меню
- 💾 **Сохранение данных** в PostgreSQL через SQLAlchemy (асинхронно)
- 📊 **Метрики Prometheus** для мониторинга
- 🐳 **Docker Compose** для лёгкого развёртывания

## Технологии

- **Python 3.11+** – язык программирования
- **aiogram 3.x** – асинхронный фреймворк для Telegram Bot API
- **SQLAlchemy 2.0** (async) – ORM для работы с базой данных
- **asyncpg** – асинхронный драйвер PostgreSQL
- **Pydantic 2.0** – валидация данных и конфигурация
- **loguru** – удобное логирование
- **httpx** – асинхронный HTTP-клиент для запросов к API Кинопоиска
- **redis** – кэширование результатов поиска
- **tenacity** – повторные попытки при сетевых ошибках
- **prometheus-client** – метрики для мониторинга
- **poetry** – управление зависимостями

## Архитектура

Проект построен на принципах **Clean Architecture** и **SOLID**:

- **domain/** – доменные сущности и интерфейсы репозиториев
- **application/** – сценарии использования (use cases)
- **infrastructure/** – адаптеры (БД, API, Telegram бот)
- **tests/** – тесты

Это обеспечивает высокую тестируемость, независимость от внешних фреймворков и лёгкую замену компонентов.

## Установка и запуск

### Требования

- Python 3.11 или выше
- PostgreSQL (или другой совместимый сервер)
- Redis (для кэширования)
- Poetry (рекомендуется) или pip
- Telegram бот (получить токен у @BotFather)
- API-ключ Kinopoisk (https://kinopoiskapiunofficial.tech/)

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourname/watchlist.git
cd watchlist

С помощью poetry:

bash
poetry install
Или с помощью pip:

bash
pip install -r requirements.txt
3. Настройка переменных окружения
Создайте файл .env в корне проекта на основе .env.example:

bash
cp .env.example .env
Заполните значения:

BOT_TOKEN – токен вашего Telegram бота

KINOPOISK_API_KEY – ключ API Кинопоиска

DATABASE_URL – строка подключения к PostgreSQL (например, postgresql+asyncpg://user:password@localhost:5432/watchlist)

REDIS_URL – строка подключения к Redis (например, redis://localhost:6379/0)

VOTE_THRESHOLD – разница голосов для принятия фильма (по умолчанию 2)

MIN_VOTERS – минимальное количество проголосовавших для принятия (по умолчанию 2)

4. Запуск PostgreSQL и Redis
Вариант A: локальные службы

bash
# PostgreSQL
sudo systemctl start postgresql   # Linux
# или
pg_ctl -D /usr/local/var/postgres start  # macOS

# Redis
redis-server
Вариант B: Docker Compose (рекомендуется)

bash
docker-compose up -d db redis
5. Создание базы данных и выполнение миграций
Если вы не используете Docker Compose, создайте базу данных вручную:

sql
CREATE USER user WITH PASSWORD 'password';
CREATE DATABASE watchlist OWNER user;
GRANT ALL PRIVILEGES ON DATABASE watchlist TO user;
Затем выполните миграции:

bash
alembic upgrade head
Если используете Docker Compose:

bash
docker-compose exec bot alembic upgrade head
6. Запуск бота
Локально:

bash
python -m Watchlist.main
Или с poetry:

bash
poetry run python -m Watchlist.main
Через Docker Compose:

bash
docker-compose up -d bot
7. Проверка работы
Откройте Telegram, найдите бота по его username

Отправьте /start – бот ответит приветствием

Используйте /search для поиска фильмов

Добавьте фильм в очередь и проголосуйте

Команда /queue покажет текущую очередь

Команда /history покажет историю просмотренных фильмов

При достижении порога голосов бот отправит уведомление с ссылками на кинотеатры

8. Мониторинг
Метрики Prometheus доступны по адресу http://localhost:9090/metrics:

bot_requests_total – количество запросов по командам

bot_votes_total – количество голосов

bot_search_duration_seconds – время выполнения поиска

Логи пишутся в файл logs/bot.log с ежедневной ротацией.

Команды бота
Команда	Описание
/start	Начать работу, показать главное меню
/search	Поиск фильмов по названию
/queue	Показать текущую очередь
/history	Показать историю просмотренных фильмов
/help	Показать справку
Также доступны кнопки в главном меню: 🔍 Поиск, 📋 Очередь, ❓ Помощь.

Голосование и принятие
Каждый добавленный фильм имеет кнопки голосования 👍 За / 👎 Против

Голос можно изменить в любой момент

Фильм автоматически принимается, когда:

Разница голосов За и Против достигает VOTE_THRESHOLD

Общее количество проголосовавших не меньше MIN_VOTERS

Принятый фильм сохраняется в историю, в чат отправляется уведомление с ссылками на поиск в кинотеатрах

Тестирование
Запуск тестов:

bash
poetry run pytest -v
Тесты используют отдельную базу данных, определённую в pyproject.toml. Убедитесь, что тестовая БД существует.

Дальнейшее развитие
Вынести уведомления в отдельный интерфейс INotificationService (DI)

Оптимизировать /history с использованием JOIN

Поддержка групповых чатов (отслеживание участников)

Рекомендации на основе истории просмотров

Интеграция с онлайн-кинотеатрами через прямые ссылки на фильмы

Добавление жанров и рекомендаций по жанрам

Webhook вместо поллинга для масштабирования

Лицензия
Проект распространяется под лицензией MIT. Подробности в файле LICENSE.

Watchlist – делайте выбор фильмов вместе, быстро и удобно! 🎬``