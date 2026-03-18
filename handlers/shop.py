# handlers/shop.py

class Shop:
    def __init__(self):
        self.categories = self.load_categories()
        self.products = self.load_products()

    def load_categories(self):
        # Load categories from the database or API
        return ['Electronics', 'Clothing', 'Books']

    def load_products(self):
        # Load products from the database or API
        return {
            'Electronics': ['Smartphone', 'Laptop', 'Headphones'],
            'Clothing': ['T-shirt', 'Jeans', 'Jacket'],
            'Books': ['Novel', 'Science', 'History']
        }

    def get_product_details(self, category, product):
        # Get details for a specific product
        return {
            'Smartphone': {'price': 299.99, 'description': 'Latest model smartphone'},
            'Laptop': {'price': 799.99, 'description': 'High performance laptop'},
            'Headphones': {'price': 99.99, 'description': 'Noise-cancelling headphones'},
            'T-shirt': {'price': 19.99, 'description': 'Cotton t-shirt'},
            'Jeans': {'price': 49.99, 'description': 'Stylish jeans'},
            'Jacket': {'price': 79.99, 'description': 'Winter jacket'},
            'Novel': {'price': 15.99, 'description': 'Fiction novel'},
            'Science': {'price': 25.99, 'description': 'Science book'},
            'History': {'price': 20.99, 'description': 'History book'},
        }.get(product)

    def select_quantity(self, product, quantity):
        # Logic for selecting the quantity
        return quantity

    def process_payment(self, total_amount):
        # Integration with payment gateway
        return "Payment processed successfully for ${:.2f}".format(total_amount)

# Example usage
if __name__ == "__main__":
    shop = Shop()
    category = 'Electronics'
    product = 'Smartphone'
    quantity = 2
    details = shop.get_product_details(category, product)
    total_amount = details['price'] * quantity
    payment_status = shop.process_payment(total_amount)
    print(payment_status)