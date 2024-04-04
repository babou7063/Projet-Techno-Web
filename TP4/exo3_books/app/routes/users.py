from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.user import check_user,get_user_by_email,update_user_group,update_user_status,get_all_users
from typing import Annotated
from app.login_manager import login_manager
from app.database import database
from app.schemas.user import User
router = APIRouter(tags=["Books"])
templates = Jinja2Templates(directory="templates")

@router.get('/login')
def display_login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        context={'request': request}
    )

@router.get('/logout')
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(login_manager.cookie_name, path='/')
    return response

@router.post('/login')
def login(email: Annotated[str, Form()],password: Annotated[str, Form()]):
    
    log,user = check_user(email,password)
    
    if not log or (log is None):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vos identifiants sont incorrecte réessayez"

        )
    if  user["status"] == "blocked":
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vous avez été bloqué sur cette page."
        )
    access_token = login_manager.create_access_token(data={'sub': str(user['id'])})
    
    # Redirection avec le cookie de session
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key=login_manager.cookie_name, value=access_token, httponly=True)
    return response


@router.get('/login_admin')
def display_login_page(request: Request):
    return templates.TemplateResponse(
        "login_admin.html",
        context={'request': request}
    )

@router.post('/login_admin')
def login(email: Annotated[str, Form()],password: Annotated[str, Form()]):
    
    log,user = check_user(email,password)
    
    if not log or (log is None):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vos identifiants sont incorrecte reessayez"
        )
    
    if user["group"] == "admin":
        access_token = login_manager.create_access_token(data={'sub': str(user['id'])})
        # Redirection avec le cookie de session
        response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key=login_manager.cookie_name, value=access_token, httponly=True)
        return response
    
    else:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vous n'appartenez pas au group 'admin'"
        )


@router.get('/signup')
def display_signup_page(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        context={'request': request}
    )


@router.post('/signup')
def create_user(firstname: Annotated[str, Form()],lastname: Annotated[str, Form()],email: Annotated[str, Form()],password: Annotated[str, Form()]):

    new_user_data = {
    "id":str(uuid4()),
    "first_name":firstname.strip(),
    "last_name": lastname.strip(),
    "email": email.strip(),
    "password":password.strip(),
    "status": "okay",
    "group":"client"
    }

    # Vérification si l'utilisateur existe déjà
    for existing_user in database["users"]:
        if existing_user["email"] == new_user_data["email"]:
            raise HTTPException(status_code=401, detail="Email déjà enregistré.")

    database["users"].append(new_user_data)
    return RedirectResponse(url="/", status_code=302)


@router.get('/modify_status/{email}')
def ask_to_modifyu(email: str, request: Request, user=Depends(login_manager)):
    if user.group == "admin":
      
        users = get_user_by_email(email)
        
        return templates.TemplateResponse(
            "modify_status.html",
            context={'request': request,'user':users}
        )
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")


@router.post('/modify_status/{email}')
def modify_user(email:str,status: Annotated[str, Form()],user=Depends(login_manager)):
    if user.group == "admin":
        updated_user = update_user_status(email,status.strip())

        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No User found with this email.",
            )

        return RedirectResponse(url="/admin", status_code=302)
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")


@router.get('/modify_group/{email}')
def ask_to_modifyg(email: str, request: Request, user=Depends(login_manager)):
    if user.group == "admin":
        users = get_user_by_email(email)
        
        return templates.TemplateResponse(
            "modify_group.html",
            context={'request': request,'user':users}
        )
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")


@router.post('/modify_group/{email}')
def modify_group(email: str,group: Annotated[str, Form()],user=Depends(login_manager)):
    if user.group == "admin":
        updated_user = update_user_group(email,group.strip())

        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No User found with this email.",
            )

        return RedirectResponse(url="/admin", status_code=302)
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")

@router.get('/admin')
def get_all_userss(request: Request,user=Depends(login_manager)):
    if user.group == "admin":
        users = get_all_users()
        return templates.TemplateResponse("display_users.html", context={'request': request, 'users': users})
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")