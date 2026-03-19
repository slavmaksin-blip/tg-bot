# tg-bot

Telegram-бот с магазином, оплатой через CryptoBot и xRocket, профилем пользователя и панелью администратора.

## Возможности

| Раздел | Описание |
|---|---|
| 🛍 Магазин | Категории → товары → покупка |
| 💳 Оплата | CryptoBot и xRocket (USDT) с автоматической проверкой |
| 👤 Профиль | Информация о пользователе и история заказов |
| 🔧 Админ-панель | Добавление категорий/товаров, просмотр заказов/пользователей, массовая рассылка |

## Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/slavmaksin-blip/tg-bot.git
cd tg-bot

# 2. Создай виртуальное окружение и установи зависимости
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка

Открой `config.py` и заполни параметры:

| Параметр | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_IDS` | Список Telegram ID администраторов |
| `CHANNEL_USERNAME` | Username канала для проверки подписки (`@channel`) или `None` |
| `CHANNEL_LINK` | Ссылка на канал, показываемая пользователям |
| `CRYPTOBOT_API_KEY` | API-ключ CryptoBot (https://t.me/CryptoBot) |
| `XROCKET_API_KEY` | API-ключ xRocket (https://t.me/xRocket) |
| `DATABASE_PATH` | Путь к файлу SQLite (по умолчанию `bot.db`) |
| `PAYMENT_CURRENCY` | Валюта оплаты (`USDT`, `TON`, и т.д.) |

## Запуск

```bash
python main.py
```

## Команды бота

### Для всех пользователей
| Команда | Описание |
|---|---|
| `/start` | Запустить бота / главное меню |
| `/help` | Справка |

### Только для администраторов
| Команда | Описание |
|---|---|
| `/admin` | Открыть панель администратора |
| `/add_category` | Добавить категорию |
| `/add_product` | Добавить товар (с прикреплением файла) |
| `/broadcast` | Рассылка сообщения всем пользователям |
| `/cancel` | Отменить текущее действие |

## Структура проекта

```
tg-bot/
├── config.py              # Конфигурация
├── database.py            # SQLite: пользователи, категории, товары, заказы
├── main.py                # Точка входа
├── requirements.txt       # Зависимости
├── handlers/
│   ├── start.py           # /start, /help, проверка подписки
│   ├── shop.py            # Магазин
│   ├── payments.py        # Оплата (CryptoBot, xRocket)
│   ├── admin.py           # Админ-панель
│   └── profile.py         # Профиль пользователя
└── utils/
    └── file_handler.py    # Утилиты для загрузки файлов
```
