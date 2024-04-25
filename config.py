import os
import secrets


class AppConfig:
    SECRET_KEY = secrets.token_urlsafe(32)
    SQLALCHEMY_DATABASE_URI = (f'sqlite:////'
                               f'{os.path.abspath(os.getcwd()).replace("\\", "/")[3:]}/'
                               f'database.db')
