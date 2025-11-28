import jwt
from passlib.hash import bcrypt

from app.core import ms_config


def sign_jwt_dict(data: dict) -> str:
    return jwt.encode(data, ms_config.jwt.auth_private_key, algorithm=ms_config.jwt.algorithm)


def hash_password(password: str, rounds=12) -> str:
    return bcrypt.using(rounds=rounds).hash(password)


def verify_password(password: str, hash: str) -> bool:
    return bcrypt.verify(password, hash)
