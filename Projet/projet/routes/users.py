from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import  RedirectResponse
from fastapi.templating import Jinja2Templates
from projet.services.users import get_token, verify_password,hash_password
from typing import Annotated
from projet.login_manager import login_manager
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import smtplib
router = APIRouter(tags=["Users"])
templates = Jinja2Templates(directory="projet/templates")

from sqlalchemy.orm import Session
from projet.models import User as UserModel
from projet.models import Token
from projet.database import SessionLocal
from projet.schemas import EmailSchema
from projet.services.reset import p

@router.post('/login')
def login(email: str = Form(), password: str = Form()):
    """
    Handles user login. Validates user credentials and sets a session cookie if successful.

    Parameters:
    - email (str): The email address of the user trying to log in.
    - password (str): The password for the account.

    This function first checks the user's existence in the database using their email.
    Then it verifies the password. If either check fails, an HTTP 401 Unauthorized exception is raised.
    A blocked user also receives an HTTP 401 Unauthorized response.
    On successful validation, a session cookie is set, and the user is redirected to the homepage.
    """

    # Start a new database session
    db: Session = SessionLocal()

    # Query the database for the user by email
    user = db.query(UserModel).filter(UserModel.email == email).first()

    # Check if user exists and password is correct
    if not user or not verify_password(password, user.password):
        # Raise an exception if authentication fails
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vos identifiants sont incorrects."
        )

    # Check if the user is blocked
    if user.status == False:
        # Raise an exception if user is blocked
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vous avez été bloqué sur cette page."
        )

    # Generate an access token for the user
    access_token = login_manager.create_access_token(data={'sub': str(user.id)})
    
    # Create a redirect response to the homepage
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    # Set the session cookie with the access token
    response.set_cookie(key=login_manager.cookie_name, value=access_token, httponly=True)

    # Close the database session
    db.close()

    # Return the response, which redirects the user to the homepage
    return response


@router.get('/login')
def display_login_page(request: Request):
    """ Display the login page
     Parameters:
        - request: The incoming request object.
    
    """
    return templates.TemplateResponse(
        "login.html",
        context={'request': request}
    )

@router.get('/logout')
def logout():
    """Log out an User
     Parameters:
        - request: The incoming request object.
    """
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(login_manager.cookie_name, path='/')
    return response


async def get_current_user_admin(request: Request):
    """
    Async function to get the current user and check if they are an admin.

    Parameters:
    - request: The incoming request object.

    Returns the user if they are logged in and an admin, otherwise None.
    """

    try:
        # Retrieve the current user from the session using login_manager
        user = await login_manager(request)
        # Check if the user exists and is an admin
        if user and user.group == "admin":
            return user
        return None
    except Exception:
        # Return None in case of any exception
        return None

@router.get('/login_admin')
async def display_login_page(request: Request):
    """
    Displays the admin login page or redirects an already logged-in admin to the admin panel.

    Parameters:
    - request: The incoming request object.

    If an admin is already logged in, redirects to the admin panel. 
    Otherwise, it renders the admin login page.
    """

    user = await get_current_user_admin(request)
    if user:
        # Redirect to the admin panel if already logged in as admin
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    
    # Render the admin login page for non-authenticated or non-admin users
    return templates.TemplateResponse("login_admin.html", context={'request': request})




@router.post('/login_admin')
def login_admin(email: str = Form(), password: str = Form()):
    """
    Handles admin login.

    Parameters:
    - email: Admin's email.
    - password: Admin's password.

    Verifies admin credentials. If successful, sets a session cookie and redirects to the admin panel.
    Raises HTTP 401 Unauthorized for incorrect credentials or non-admin users.
    """

    db: Session = SessionLocal()
    try:
        # Query for the user by email
        user = db.query(UserModel).filter(UserModel.email == email).first()
        # Check for valid user and password match
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vos identifiants sont incorrects."
            )
        # Ensure the user belongs to the admin group
        if user.group != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vous n'appartenez pas au groupe 'admin'."
            )
        # Check if the user is blocked
        if user.status == False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vous avez été bloqué sur cette page."
            )
        # Generate an access token for the user
        access_token = login_manager.create_access_token(data={'sub': str(user.id)})
        # Set the session cookie with the access token and redirect to admin panel
        response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key=login_manager.cookie_name, value=access_token, httponly=True)
        return response
    finally:
        # Close the database session
        db.close()


@router.get('/signup')
def display_signup_page(request: Request):
    """Display Signup form for User
     Parameters:
        - request: The incoming request object.
    """
    return templates.TemplateResponse(
        "signup.html",
        context={'request': request}
    )


@router.post('/signup')
def create_user(firstname: str = Form(), lastname: str = Form(), email: str = Form(), password: str = Form()):
    """
    Registers a new user.

    Parameters:
    - firstname: The first name of the user.
    - lastname: The last name of the user.
    - email: The email address of the user. It must be unique.
    - password: The password for the user account.

    This function checks if the email is already registered. If not, it creates a new user with a hashed password.
    New users are set as 'admin' by default.
    """

    db: Session = SessionLocal()
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà enregistré.")

    # Create a new user with hashed password
    new_user = UserModel(
        id=str(uuid4()),
        first_name=firstname,
        last_name=lastname,
        email = email,
        password= hash_password(password),  # Hash the password
        is_active =True,
        group="client"  # Set user group as client / you can change as admin to have full right
    )
    db.add(new_user)
    db.commit()
    # Redirect to the homepage after successful registration
    return RedirectResponse(url="/", status_code=302)




@router.get("/change_password")
def change_password(request:Request,user = Depends(login_manager)):
    """Display the templates for the password change
    parameter:
    - resquest: The incoming HTTP request"""
    return templates.TemplateResponse("changepassword.html", context={'request': request, 'users': user})

@router.get("/forgot_password")
def change_password(request:Request):
    """Display the templates for the password change
    parameter:
    - resquest: The incoming HTTP request"""
    return templates.TemplateResponse("passwordfogot.html", context={'request': request})


@router.post("/forgot_password")
async def simple_send(request:Request,email:str = Form()):
    
    db = SessionLocal()
    token_str = str(uuid4)
    token = Token(token=token_str, user_email=email)
    db.add(token)
    db.commit()

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email],
        body=p.format(token_str),
        subtype=MessageType.html)
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
        smtp.login("projetjournal91@gmail.com","++projetjournal91")
        smtp.send_message(message)

    return templates.TemplateResponse("passwordfogot.html", context={'request': request,"message": "email has been sent"})


@router.get("/forgot_password/{token}")
def change(request:Request,token: str):
    db = SessionLocal()
    id = get_token(db,token) 
    if id != None:
        return templates.TemplateResponse("changepassword.html", context={'request': request, 'users': db.query(UserModel).filter(UserModel.id == id).first()})

    raise HTTPException(status_code=400, detail="tokens non valide , le lien doit avoir expriré veileuz réessayez depuis le debut.")


@router.post("/change/{user}")
def change(request:Request, user, new_password: str = Form(), confirm_new_password: str = Form()):
    db = SessionLocal()
    try:
        db_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if new_password != confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        db_user.password = hash_password(new_password) 
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

    return templates.TemplateResponse("/", context={'user': user, 'request':request, "message": "Password changed successfully"})

