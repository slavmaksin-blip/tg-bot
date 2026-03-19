# config.py

# Telegram Bot Configuration
BOT_TOKEN = 'your_bot_token_here'           # @BotFather token
ADMIN_IDS = [12345678, 87654321]            # Telegram user IDs of admins
CHANNEL_USERNAME = '@your_channel'          # Channel username for subscription check (or None to disable)
CHANNEL_LINK = 'https://t.me/your_channel'  # Channel invite link shown to users

# CryptoBot API Configuration (https://help.crypt.bot/crypto-pay-api)
CRYPTOBOT_API_URL = 'https://pay.crypt.bot/api'  # Use https://testnet-pay.crypt.bot/api for testnet
CRYPTOBOT_API_KEY = 'your_cryptobot_api_key_here'

# xRocket API Configuration (https://xrocket.tg/docs)
XROCKET_API_URL = 'https://pay.xrocket.tg'
XROCKET_API_KEY = 'your_xrocket_api_key_here'

# Database Path
DATABASE_PATH = 'bot.db'

# Payment check interval (seconds) — how often the bot checks if invoices are paid
PAYMENT_CHECK_INTERVAL = 30

# Currency for payments (USDT, TON, BTC, ETH, etc.)
PAYMENT_CURRENCY = 'USDT'
