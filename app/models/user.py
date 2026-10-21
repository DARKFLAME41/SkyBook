from flask_login import UserMixin
from bson import ObjectId
from .. import mongo, login_manager


class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.name = user_doc["name"]
        self.email = user_doc["email"]
        self.role = user_doc.get("role", "user")

    def is_admin(self):
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id):
    user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return User(user_doc)
    return None


def get_user_by_email(email):
    return mongo.db.users.find_one({"email": email})


def create_user(name, email, password_hash, role="user"):
    user = {
        "name": name,
        "email": email,
        "password": password_hash,
        "role": role,
    }
    result = mongo.db.users.insert_one(user)
    return result.inserted_id
