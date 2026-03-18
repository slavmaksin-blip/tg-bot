class UserProfile:
    def __init__(self, username, purchase_history):
        self.username = username
        self.purchase_history = purchase_history

    def show_profile(self):
        profile_info = f"Username: {self.username}\nPurchase History:\n"
        for purchase in self.purchase_history:
            profile_info += f"- {purchase}\n"
        return profile_info

# Example usage:
if __name__ == '__main__':
    user = UserProfile('user123', ['item1', 'item2', 'item3'])
    print(user.show_profile())