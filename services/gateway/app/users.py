# services/gateway/app/users.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db = {
    "admin_ds": {
        "username": "admin_ds",
        "email": "admin@datascientest.com",
        "hashed_password": "$2b$12$I113P5FfCbZcAeDvBWwQMO4xP0nWsFVK1JfdgqtsYsczpyKRn6uGq",
        "role": "admin",
    },
    "user_ds": {
        "username": "user_ds",
        "email": "user@datascientest.com",
        "hashed_password": "$2b$12$u14fiZWxoEDTtX48dNItouNbP7AxT3FOg1ZJDy38kTc5fTpCH8AQ2",
        "role": "user",
    },
}
