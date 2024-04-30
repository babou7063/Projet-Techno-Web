from fastapi_login import LoginManager
from projet.database import SessionLocal
from projet.models import User as UserModel


SECRET = "SECRET"
login_manager = LoginManager(SECRET, '/login', use_cookie=True)
login_manager.cookie_name = "auth_cookie"


@login_manager.user_loader()
def query_user(user_id: str):
    db = SessionLocal()
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    return user
