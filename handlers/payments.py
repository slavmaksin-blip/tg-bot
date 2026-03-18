# payment.py

class PaymentProcessor:
    def __init__(self, crypto_bot_api_key, xrocket_api_key):
        self.crypto_bot_api_key = crypto_bot_api_key
        self.xrocket_api_key = xrocket_api_key

    def process_crypto_payment(self, amount, user_id):
        # Logic for processing payment via CryptoBot API
        pass

    def process_xrocket_payment(self, amount, user_id):
        # Logic for processing payment via xRocket API
        pass

    def verify_payment(self, transaction_id):
        # Auto-verification logic for both payment methods
        pass

# Example usage:
# processor = PaymentProcessor('your_crypto_bot_api_key', 'your_xrocket_api_key')
# processor.process_crypto_payment(100, user_id)
# processor.process_xrocket_payment(100, user_id)