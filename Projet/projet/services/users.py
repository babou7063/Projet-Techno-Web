from passlib.context import CryptContext
from sqlalchemy.orm import Session
from projet.models import Token


# Configuration du contexte de hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str):
    """
    Hashes a password using the configured password hashing context.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        str: The hashed password.
    """
    # Hash the password using the configured password hashing context
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str):
    """
    Verifies if a plain text password matches a hashed password.

    Args:
        plain_password (str): The plain text password to be verified.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plain text password matches the hashed password, False otherwise.
    """
    # Verify the plain text password against the hashed password using the configured password hashing context
    return pwd_context.verify(plain_password, hashed_password)



def get_token(db: Session, token_str: str):
    """
    Retrieves a token from the database based on the given token string.

    Args:
        db (Session): The database session.
        token_str (str): The token string to search for.

    Returns:
        Optional[str]: The user email associated with the token if it exists and has not expired,
        otherwise None.
    """
    # Query the database for the token
    token = db.query(Token).filter(Token.token == token_str).first()

    # Check if the token exists and has not expired
    if token and not token.is_expired():
        # Return the user email associated with the token
        return token.user_email

    # Return None if the token does not exist or has expired
    return None

