from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.user import check_user
from typing import Annotated
from app.login_manager import login_manager

router = APIRouter(tags=["Books"])
templates = Jinja2Templates(directory="templates")

@router.get('/login')
def display_login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        context={'request': request}
    )

@router.post('/login')
def login(email: Annotated[str, Form()],password: Annotated[str, Form()]):
    
    log,user = check_user(email,password)
    
    if not log or (log is None):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Veuillez vous connecter pour accéder à cette page"
        )
    access_token = login_manager.create_access_token(data={'sub': str(user['id'])})
    
    # Redirection avec le cookie de session
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key=login_manager.cookie_name, value=access_token, httponly=True)
    return response


