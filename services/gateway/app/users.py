

# services/gateway/app/users.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@datascientest.com",
        "hashed_password": "$2b$12$1mS5QX21cc7FTpHsP7hSVOUkYpykVPZ7UlpgQHW8T9fxnQLg3cPpe",
        "role": "admin",
    },
    "user": {
        "username": "user",
        "email": "user@datascientest.com",
        "hashed_password": "$2b$12$KTu75qN/cLyftVsf75TNgeVOcBqZdDXPW3Np8nJLde5sMLsJncesi",
        "role": "user",
    },
}
