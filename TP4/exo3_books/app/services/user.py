from app.database import database
from app.schemas.user import User


def get_user_by_email(email: str):
    for user in database['users']:
        if user['email'] == email:
            return user
    return None


def get_user_by_id(id: str):
    for user in database['users']:
        if user['id'] == id:
            return User.model_validate(user)
    return None


def check_user(email:str,password:str):

    user = get_user_by_email(email)

    if user is None: return None , user

    if user["password"] == password : return True,user

    else: return False,user
