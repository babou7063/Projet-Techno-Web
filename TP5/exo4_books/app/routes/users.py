from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.user import verify_password,hash_password
from typing import Annotated
from app.login_manager import login_manager
from app.schemas.user import User
router = APIRouter(tags=["Books"])
templates = Jinja2Templates(directory="templates")


from sqlalchemy.orm import Session
from app.models.users import User as UserModel
from app.database import SessionLocal

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
    if user.status == "blocked":
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
        if user.status == "blocked":
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
        email=email,
        password= hash_password(password),  # Hash the password
        status="active",
        group="client"  # Set user group as client / you can change as admin to have full right
    )
    db.add(new_user)
    db.commit()
    # Redirect to the homepage after successful registration
    return RedirectResponse(url="/", status_code=302)




@router.get('/modify_status/{email}')
def ask_to_modifyu(email: str, request: Request, user=Depends(login_manager)):
    """
    Displays a page for modifying a user's status. Only accessible to admins.

    Parameters:
    - email: Email of the user to be modified.
    - request: The incoming request object.
    - user: The currently logged-in user.

    This function checks if the current user is an admin and displays the modification page.
    If not an admin, an error is raised.
    """

    if user.group == "admin":
        db: Session = SessionLocal()
        # Query the user by email
        users= db.query(UserModel).filter(UserModel.email == email).first()
        db.close()
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
    """
    Modifies a user's status (e.g., active, blocked). Only accessible to admins.

    Parameters:
    - email: Email of the user to be modified.
    - status: New status to be applied.
    - user: The currently logged-in user.

    This function updates the status of a specified user, provided the logged-in user is an admin.
    """

    if user.group == "admin":
        db: Session = SessionLocal()
        # Query the user by email
        user_to_update = db.query(UserModel).filter(UserModel.email == email).first()
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the status
        user_to_update.status = status
        db.commit()
        return RedirectResponse(url="/admin", status_code=302)
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")




@router.get('/modify_group/{email}')
def ask_to_modifyg(email: str, request: Request, user=Depends(login_manager)):
    """
    Displays a page for modifying a user's group (e.g., admin, client). Only accessible to admins.

    Parameters:
    - email: Email of the user to be modified.
    - request: The incoming request object.
    - user: The currently logged-in user.

    Renders a template for changing a user's group if the current user is an admin.
    """

    if user.group == "admin":
        db: Session = SessionLocal()
        # Query the user by email
        users= db.query(UserModel).filter(UserModel.email == email).first()
        db.close()
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
    """
    Modifies a user's group (e.g., admin, client). Only accessible to admins.

    Parameters:
    - email: Email of the user to be modified.
    - group: New group to be applied.
    - user: The currently logged-in user.

    This function updates the group of a specified user, provided the logged-in user is an admin.
    """

    if user.group == "admin":
        db: Session = SessionLocal()
        # Query the user by email
        user_to_update = db.query(UserModel).filter(UserModel.email == email).first()
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the group
        user_to_update.group = group
        db.commit()
        return RedirectResponse(url="/admin", status_code=302)
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")


@router.get('/admin')
def get_all_userss(request: Request,user=Depends(login_manager)):
    """
    Fetches and displays all users. Accessible only to admins.
    Parameters:
    - request: The incoming HTTP request.
    - user: The currently logged-in user, verified as an admin.
    
    If the user is an admin, it queries the database for all users and returns a page listing them.
    If not an admin, an error is raised.
    """

    if user.group == "admin":
        db: Session = SessionLocal()
        users = db.query(UserModel).all()
        db.close()
        return templates.TemplateResponse("display_users.html", context={'request': request, 'users': users})
    else:
        raise HTTPException(
            status_code=401,
           detail=" vous n'êtes pas administrateur. vous ne pouvez pas consulter cette page")


@router.post("/change_password")
def change_password(request:Request,old_password: str = Form(), new_password: str = Form(), confirm_new_password: str = Form(), user=Depends(login_manager)):
    """
    Changes the password of the current user.
    Parameters:
    - request: The incoming HTTP request.
    - old_password: The user's current password.
    - new_password: The new password the user wants to set.
    - confirm_new_password: Confirmation of the new password.
    - user: The currently logged-in user.

    Verifies the old password, checks if the new passwords match, and updates the password in the database.
    """

    db = SessionLocal()
    try:
        db_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(old_password, db_user.password):
            raise HTTPException(status_code=400, detail="Invalid old password")

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

@router.get("/change_password")
def change_password(request:Request,user = Depends(login_manager)):
    """Display the templates for the password change
    parameter:
    - resquest: The incoming HTTP request"""
    return templates.TemplateResponse("changepassword.html", context={'request': request, 'users': user})

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
