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
def login(email: str = Form(), password: str = Form(),db: Session = Depends(get_db)):
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
def create_user(firstname: str = Form(), lastname: str = Form(), email: str = Form(), password: str = Form(),db: Session = Depends(get_db)):
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
    """
    Retrieves the articles of a specific author and renders the 'articleAuthors.html' template.

    Parameters:
    - request: The incoming HTTP request.
    - author_id: The ID of the author.
    - db: The database session.

    Returns:
    - A TemplateResponse object with the rendered 'articleAuthors.html' template.
    """
    # Retrieve the author object from the database
    author = db.query(UserModel).get(author_id)

    # Retrieve the articles of the author from the database
    articles = db.query(ArticleModel).filter(ArticleModel.author_id == author_id).all()

    # Render the 'articleAuthors.html' template with the author and articles
    return templates.TemplateResponse(
        "articleAuthors.html",
        context={
            'request': request,  # Include the request object in the context
            'author': author,  # Include the author object in the context
            'articles': articles,  # Include the articles in the context
        }
    )
    

@router.get("/subscribe/{author_id}")
def subscribe_author(
    author_id: str, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)
):
    """
    Subscribe the user to an author.

    Parameters:
    - author_id: The ID of the author to subscribe to.
    - db: The database session.
    - user: The logged-in user.

    Returns:
    - A RedirectResponse to the author's page with a success message if the subscription is successful,
      or an error message if the user is subscribing to themselves or if the user is already subscribed.
    """
    # Check if the user is trying to subscribe to themselves
    if user.id == author_id:
        return RedirectResponse(
            url="/author?message=You cannot subscribe to yourself", status_code=302
        )

    # Check if the user is already subscribed to the author
    already = db.query(SubscriptionModel).filter_by(user_id=user.id, author_id=author_id).first()
    if already is not None:
        return RedirectResponse(
            url="/author?message=Already subscribed", status_code=302
        )

    # Create a new subscription and add it to the database
    subscription = SubscriptionModel(user_id=user.id, author_id=author_id)
    db.add(subscription)
    db.commit()

    # Redirect to the author's page with a success message
    return RedirectResponse(
        url="/author?message=Subscription successful", status_code=302
    )

@router.post("/unsubscribe/{author_id}")
def unsubscribe_author(author_id: str, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)):
    """
    Unsubscribe the user from an author.

    Parameters:
    - author_id: The ID of the author to unsubscribe from.
    - db: The database session.
    - user: The logged-in user.

    Returns:
    - A RedirectResponse to the subscriptions page with a success message if the unsubscription is successful,
      or an error message if the user is trying to unsubscribe themselves.
    """
    # Find the subscription to delete
    subscription = db.query(SubscriptionModel).filter_by(user_id=user.id, author_id=author_id).first()

    # Check if the user is trying to unsubscribe to themselves
    if not subscription:
        return RedirectResponse(
            url="/subscriptions?message=You cannot unsubscribe yourself", status_code=302
        )

    # Delete the subscription and commit the changes to the database
    db.delete(subscription)
    db.commit()

    # Redirect to the subscriptions page with a success message
    return RedirectResponse(
        url="/subscriptions?message=Unsubscription successful", status_code=302
    )


@router.get("/subscriptions")
def subscriptions(request: Request, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)):
    """
    Retrieve the list of authors the user is subscribed to.

    Parameters:
    - request: The incoming request object.
    - db: The database session.
    - user: The logged-in user.

    Returns:
    - A TemplateResponse object with the subscriptions.html template and the authors list as context.
    """
    # Query the database for the subscriptions of the user
    subscriptions = db.query(SubscriptionModel).filter_by(user_id=user.id).all()

    # Extract the authors from the subscriptions
    authors = [sub.author for sub in subscriptions]

    # Return the subscriptions template with the authors list as context
    return templates.TemplateResponse(
        "subscriptions.html",
        context={'request': request, 'authors': authors}
    )

@router.get("/subscribers")
def get_subscribers(
    request: Request, db: Session = Depends(get_db), user: UserModel = Depends(login_manager)
):
    """
    Retrieve the list of subscribers for the author or verify that the logged-in user has permission.

    Parameters:
    - request: The incoming request object.
    - db: The database session.
    - user: The logged-in user.

    Returns:
    - A TemplateResponse object with the subscribers.html template and the subscribers list as context.
    """

    # Retrieve the subscriptions for the author
    subscriptions = db.query(SubscriptionModel).filter_by(author_id=user.id).all()
    subscribers = [sub.user for sub in subscriptions]

    return templates.TemplateResponse(
        "subscribers.html",
        context={'request': request, 'subscribers': subscribers}
    )



@router.get("/author")
def get_author(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retrieve the list of authors based on a query string.

    Parameters:
    - request: The incoming request object.
    - q: The query string to search for authors.
    - db: The database session.

    Returns:
    - A TemplateResponse object with the author.html template and the authors list as context.
    """
    # Check if a query string is provided
    if q:
        # Query the database for authors with first or last name containing the query string
        authors = db.query(UserModel).filter(
            or_(
                UserModel.first_name.contains(q),
                UserModel.last_name.contains(q)
            )
        ).all()
    else:
        # Query the database for all authors associated with at least one article
        authors = db.query(UserModel).join(ArticleModel).distinct(UserModel.id).all()
    
    # Return the author template with the authors list and query as context
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
async def simple_send(request:Request,email:str = Form(),db: Session = Depends(get_db)):
    """
    This function handles the POST request for the forgot password form.
    It sends an email with a reset password link to the user's email address.
    
    Parameters:
    - request: The incoming HTTP request.
    - email: The user's email address.
    - db: The database session.
    
    Returns:
    - A TemplateResponse object with the passwordfogot.html template and a message as context.
    """
    
    # Check if the user exists in the database
    if db.query(UserModel).filter(UserModel.email == email).first() == None:
        # If the user does not exist, display an error message
        return templates.TemplateResponse("passwordfogot.html", context={'request': request,"message": "Your are not in our database user. Please create a new account instead."})
    
    # Generate a unique token
    token_str = str(uuid4())
    
    # Create a Token object with the token and user email
    token = Token(token=token_str, user_email=email)
    
    # Add the Token object to the database
    db.add(token)
    db.commit()
    
    # Create a message with the reset password link
    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email],
        body=p.format(token_str),
        subtype=MessageType.html)
      
    # Create a FastMail object with the SMTP configuration
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
    
    # Send the email with the reset password link
    await fm.send_message(message)
    
    # Return a success message
    return templates.TemplateResponse("passwordfogot.html", context={'request': request,"message": "email has been sent"})


@router.get("/reset_password/{token}")
def change(request:Request,token: str,db: Session = Depends(get_db)):
    """
    This function handles the GET request for the reset password form.
    It checks if the token is valid and returns the change password form with the user's email.
    
    Parameters:
    - request: The incoming HTTP request.
    - token: The reset password token.
    - db: The database session.
    
    Returns:
    - A TemplateResponse object with the changepassword.html template and the user's email as context.
    
    Raises:
    - HTTPException: If the token is not valid.
    """
    
    # Get the user's email from the token
    email = get_token(db,token) 
    
    # Check if the token is valid
    if email is not None:
        # If the token is valid, return the change password form with the user's email
        return templates.TemplateResponse("changepassword.html", context={'request': request, 'users': db.query(UserModel).filter(UserModel.email == email).first()})
    
    # If the token is not valid, raise an HTTPException
    raise HTTPException(status_code=400, detail="Invalid token. The link may have expired. Please try again from the beginning.")
    
@router.get("/change")
def change(request:Request,user = Depends(login_manager)):
    """
    This function handles the GET request for the change password form.
    It returns the change password form with the user's email.
    
    Parameters:
    - request: The incoming HTTP request.
    - user: The currently logged-in user.
    
    Returns:
    - A TemplateResponse object with the changepasswordprofile.html template and the user's email as context.
    """
    
    # Return the change password form with the user's email
    return templates.TemplateResponse("changepasswordprofile.html", context={'request': request, 'users': user})


@router.post("/change/{email}")
def change(request:Request, email, new_password: str = Form(), confirm_new_password: str = Form(),db: Session = Depends(get_db)):
    """
    This function handles the POST request for the change password form.
    It changes the user's password in the database and returns the change password form with a success message.
    
    Parameters:
    - request: The incoming HTTP request.
    - email: The user's email address.
    - new_password: The new password for the user.
    - confirm_new_password: The confirmation of the new password.
    - db: The database session.
    
    Returns:
    - A TemplateResponse object with the passwordfogot.html template and a success message as context.
    
    Raises:
    - HTTPException: If the user is not found or the new passwords do not match.
    """
    
    try:
        # Get the user from the database
        db_user = db.query(UserModel).filter(UserModel.email ==email).first()
        
        # Check if the user exists
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the new passwords match
        if new_password != confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        # Change the user's password
        db_user.password = hash_password(new_password) 
        db.commit()
    except Exception as e:
        # Rollback the transaction if an error occurs
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Close the database session
        db.close()

    # Return the change password form with a success message
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
async def update_profile(
    request: Request, 
    email: str = Form(),
    first_name: str = Form(),
    last_name: str = Form(),
    user: UserModel = Depends(login_manager),
    db: Session = Depends(get_db)
):
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

    # Check if user is logged in
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé. Vous devez être Connecté")

    try:
        # Get the user from the database
        db_user = db.query(UserModel).filter(UserModel.id == user.id).first()

        # Update the user's information
        db_user.email = email
        db_user.first_name = first_name
        db_user.last_name = last_name

        # Commit the changes to the database
        db.commit()

        # Return the updated profile page
        return templates.TemplateResponse(
            "profile.html",
            context={'request': request, 'user': db_user, 'message': 'Profil mis à jour'}
        )
    except Exception as e:
        # Rollback the transaction if an error occurs
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Close the database session
        db.close()

@router.post("/changed")
def change(
    request: Request,
    new_password: str = Form(),
    confirm_new_password: str = Form(),
    user=Depends(login_manager),
    db: Session = Depends(get_db)
):
    """
    Change the user's password.

    Parameters:
    - request: The incoming HTTP request.
    - new_password: The new password for the user.
    - confirm_new_password: The confirmation of the new password.
    - user: The currently logged-in user.

    This function checks if the new password matches the confirmation of the new password.
    If the passwords match, it updates the user's password in the database and returns the profile page.
    """

    try:
        # Get the user from the database
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the new password matches the confirmation of the new password
        if new_password != confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        # Update the user's password
        db_user.password = hash_password(new_password)
        db.commit()
    except Exception as e:
        # Rollback the transaction if an error occurs
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Close the database session
        db.close()

    # Return the profile page with a success message
    return templates.TemplateResponse(
        "profile.html",
        context={'user': user, 'request': request, "message": "Password changed successfully"}
    )
    