import bcrypt
import os

class AuthManager:
    def __init__(self, password_file='/opt/kioskpi/admin_hash.txt'):
        self.password_file = password_file

    def verify_password(self, password):
        if not os.path.exists(self.password_file):
            return False
            
        try:
            with open(self.password_file, 'rb') as f:
                hashed = f.read().strip()
            return bcrypt.checkpw(password.encode('utf-8'), hashed)
        except Exception as e:
            print(f"Auth error: {e}")
            return False

    def set_password(self, new_password):
        try:
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            os.makedirs(os.path.dirname(self.password_file), exist_ok=True)
            with open(self.password_file, 'wb') as f:
                f.write(hashed)
            return True
        except Exception as e:
            print(f"Error setting password: {e}")
            return False
