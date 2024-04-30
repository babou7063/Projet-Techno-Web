from passlib.context import CryptContext
from sqlalchemy.orm import Session
from projet.models import Token


# Configuration du contexte de hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_token(db: Session, token_str: str):
    token = db.query(Token).filter(Token.token == token_str).first()
    if token and not token.is_expired():
        return token.user_id
    return None
