from typing import Annotated, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import  RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from projet.services.users import get_token, verify_password,hash_password
from typing import Annotated
from projet.login_manager import login_manager
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import smtplib
router = APIRouter(tags=["Users"])
templates = Jinja2Templates(directory="projet/templates")

from sqlalchemy.orm import Session
from projet.models import User as UserModel
from projet.models import Subscription as SubscriptionModel
from projet.models import Article as ArticleModel
from projet.models import Token
from projet.database import SessionLocal
from projet.schemas import EmailSchema
from projet.services.reset import p

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
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
    if user.is_active == False:
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

@router.get("/author/{author_id}")
def author_articles(request: Request, author_id: str, db: Session = Depends(get_db)):
    author = db.query(UserModel).get(author_id)
    articles = db.query(ArticleModel).filter(ArticleModel.author_id == author_id).all()
    return templates.TemplateResponse(
        "articleAuthors.html",
        context={
            'request': request,
            'author': author,
            'articles': articles,
        }
    )

@router.get("/subscribe/{author_id}")
def subscribe_author(author_id: str, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)):
    if user.id == author_id:
        return RedirectResponse(url="/author?message=You cannot subscribe to yourself", status_code=302)
    
    already = db.query(SubscriptionModel).filter_by(user_id=user.id, author_id=author_id).first()
    if already != None:
        return RedirectResponse(url="/author?message=Already subscribed", status_code=302)
    
    subscription = SubscriptionModel(user_id=user.id, author_id=author_id)
    db.add(subscription)
    db.commit()
    return RedirectResponse(url="/author?message=Subscription successful", status_code=302)

@router.post("/unsubscribe/{author_id}")
def unsubscribe_author(author_id: str, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)):
    subscription = db.query(SubscriptionModel).filter_by(user_id=user.id, author_id=author_id).first()
    if subscription:
        db.delete(subscription)
        db.commit()
    return RedirectResponse(url="/subscriptions", status_code=302)

@router.get("/subscriptions")
def subscriptions(request: Request, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)):
    subscriptions = db.query(SubscriptionModel).filter_by(user_id=user.id).all()
    authors = [sub.author for sub in subscriptions]
    return templates.TemplateResponse(
        "subscriptions.html",
        context={'request': request, 'authors': authors}
    )

@router.get("/subscribers")
def get_subscribers( request: Request, db: Session = Depends(get_db), user: UserModel= Depends(login_manager)):
    # Verify that the logged-in user is the author or has permission
    
    # Get the subscribers for the author
    subscriptions = db.query(SubscriptionModel).filter_by(author_id=user.id).all()
    subscribers = [sub.user for sub in subscriptions]

    return templates.TemplateResponse(
        "subscribers.html",
        context={'request': request, 'subscribers': subscribers}
    )


@router.get("/author")
def get_author(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    if q:
        authors = db.query(UserModel).filter(
            or_(
                UserModel.first_name.contains(q),
                UserModel.last_name.contains(q)
            )
        ).all()
    else:
        authors = db.query(UserModel).join(ArticleModel).distinct(UserModel.id).all()
    
    return templates.TemplateResponse(
        "author.html",
        context={'request': request, 'Authors': authors, 'query': q}
    )

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
    if db.query(UserModel).filter(UserModel.email == email).first() == None:
        return templates.TemplateResponse("passwordfogot.html", context={'request': request,"message": "Your are not in our database user. Please create a new account instead."})
    token_str = str(uuid4())
    token = Token(token=token_str, user_email=email)
    db.add(token)
    db.commit()

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email],
        body=p.format(token_str),
        subtype=MessageType.html)
      
    fm = FastMail(ConnectionConfig(
    MAIL_USERNAME ="projetjournal91@gmail.com",
    MAIL_PASSWORD = "mvrfdvklfrlvnetz",
    MAIL_FROM = "projetjournal91@gmail.com",
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True))
    await fm.send_message(message)
    return templates.TemplateResponse("passwordfogot.html", context={'request': request,"message": "email has been sent"})


@router.get("/reset_password/{token}")
def change(request:Request,token: str):
    db = SessionLocal()
    email = get_token(db,token) 
    if email != None:
        return templates.TemplateResponse("changepassword.html", context={'request': request, 'users': db.query(UserModel).filter(UserModel.email == email).first()})

    raise HTTPException(status_code=400, detail="tokens non valide , le lien doit avoir expriré veileuz réessayez depuis le debut.")

@router.get("/change")
def change(request:Request,user = Depends(login_manager)):
    return templates.TemplateResponse("changepasswordprofile.html", context={'request': request, 'users': user })


@router.post("/change/{email}")
def change(request:Request, email, new_password: str = Form(), confirm_new_password: str = Form()):
    db = SessionLocal()
    try:
        db_user = db.query(UserModel).filter(UserModel.email ==email).first()
        
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

    return templates.TemplateResponse("passwordfogot.html", context={'user': db_user, 'request':request, "message": "Password changed successfully"})

@router.get("/profile")
async def view_profile(request: Request, user: UserModel = Depends(login_manager)):
    """
    Displays the profile of the currently logged-in user.
    Parameters:
    - request: The incoming HTTP request.
    - user: The currently logged-in user.

    Returns a page showing the user's profile. If no user is logged in, an error is raised.
    """

    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé. Vous devez être Connecté.")

    return templates.TemplateResponse("profile.html", context={'request': request, 'user': user})

@router.post("/update_profile")
async def update_profile(request: Request, email: str = Form(), first_name: str = Form(), last_name: str = Form(), user: UserModel = Depends(login_manager)):
    """
    Updates the profile of the current user.
    Parameters:
    - request: The incoming HTTP request.
    - email: The new email address of the user.
    - first_name: The new first name of the user.
    - last_name: The new last name of the user.
    - user: The currently logged-in user.

    This function updates the user's profile information in the database and returns the updated profile page.
    """

    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé. Vous devez être Connecté")

    db = SessionLocal()

    try:
        db_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        db_user.email = email
        db_user.first_name = first_name
        db_user.last_name = last_name
        db.commit()

        return templates.TemplateResponse("profile.html", context={'request': request, 'user': db_user, 'message': 'Profil mis à jour'})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.post("/changed")
def change(request:Request, new_password: str = Form(), confirm_new_password: str = Form(),user=Depends(login_manager)):
    db = SessionLocal()
    try:
        db_user = db.query(UserModel).filter(UserModel.email ==user.email).first()
        
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

    return templates.TemplateResponse("profile.html", context={'user': user, 'request':request, "message": "Password changed successfully"})
