from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def hash_password(password: str) -> str:
    return password_hash.hash(password)
