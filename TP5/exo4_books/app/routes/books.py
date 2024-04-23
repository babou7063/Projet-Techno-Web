from fastapi import APIRouter, Form, HTTPException, status, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.book import Book as BookModel
from app.models.users import User as UserModel
from app.login_manager import login_manager
from typing import Optional

router = APIRouter(tags=["Books"])
templates = Jinja2Templates(directory="templates")

@router.post('/create_book/', response_class=RedirectResponse, status_code=status.HTTP_303_SEE_OTHER)
def create_new_book(ISBN: str = Form(), title: str = Form(), author: str = Form(), editor: str = Form(), price: float = Form(), user=Depends(login_manager)):
    """
    Create a new book and add it to the database.

    Parameters:
    ISBN (str): International Standard Book Number of the book.
    title (str): Title of the book.
    author (str): Author of the book.
    editor (str): Editor of the book.
    price (float): Price of the book.
    user: Current user, obtained through dependency injection.

    Returns a RedirectResponse to the '/all_books' page after creation.
    """

    # Create a new database session
    db = SessionLocal()

    try:
        # Create and add the new book to the database
        new_book = BookModel(ISBN=ISBN, title=title, author=author, editor=editor, price=price, sale=False, owner_id=user.id)
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
    except Exception as e:
        # Rollback in case of error
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Close the database session
        db.close()

    return RedirectResponse("/all_books", status_code=status.HTTP_303_SEE_OTHER)


@router.post('/modify/{ISBN}')
def modify_book(ISBN: str, title: str = Form(), author: str = Form(), editor: str = Form(), price: float = Form(), sale: bool = Form(False), user=Depends(login_manager)):
    """
    Modify an existing book's details.

    Parameters:
    ISBN (str): ISBN of the book to modify.
    title (str): New title for the book.
    author (str): New author of the book.
    editor (str): New editor of the book.
    price (float): New price of the book.
    sale (bool): Flag to indicate if the book is sold.
    user: Current user, obtained through dependency injection.

    Returns a RedirectResponse to the '/all_books' page after updating the book.
    """

    db: Session = SessionLocal()
    try:
        # Fetch the book to be updated from the database
        book_to_update = db.query(BookModel).filter(BookModel.ISBN == ISBN).first()
        if not book_to_update:
            # Book not found in database
            raise HTTPException(status_code=404, detail="Book not found")
        if book_to_update.owner_id != user.id and user.group != "admin": 
            # User not authorized to modify this book
            raise HTTPException(status_code=403, detail="Not allowed to modify this book")

        # Update the book's attributes
        book_to_update.title = title
        book_to_update.author = author
        book_to_update.editor = editor
        book_to_update.price = price
        book_to_update.sale = sale

        # Commit the changes to the database
        db.commit()
        db.refresh(book_to_update)
    except Exception as e:
        # Rollback in case of an exception
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Close the database session
        db.close()

    return RedirectResponse(url="/all_books", status_code=302)






@router.get('/')
def display_home_page(request: Request):
    """
    Display the home page.

    Parameters:
    request: Request object.

    Returns a TemplateResponse with 'home_page_login.html'.
    """
    return templates.TemplateResponse(
        "home_page_login.html",
        context={'request': request}
    )


async def get_optional_current_user(request: Request):
    """
    Get the current user if logged in, otherwise return None.

    Parameters:
    request: Request object.

    Returns the current user object or None.
    """
    try:
        user = await login_manager(request)
        return user
    except Exception:
        return None



@router.get('/all_books')
def get_all_books(request: Request, user: Optional[UserModel] = Depends(get_optional_current_user)):
    """
    Retrieves a list of books based on the user's status (admin, client, or guest).

    If the user is an admin, all books are displayed. 
    If the user is a client, only their books and those not marked as sold are displayed.
    Guests can see only books that are not marked as sold.

    Parameters:
    - request: Request object for accessing request data.
    - user: The current user if logged in, otherwise None.

    Returns a TemplateResponse rendering 'display_books.html' with the list of books.
    """

    # Start a new database session
    db = SessionLocal()

    try:
        # Determine the set of books to display based on the user's status
        if user:
            if user.group == "admin":
                # Admin can see all books
                books = db.query(BookModel).all()
            elif user.group == "client":
                # Clients see their own books and unsold books
                books = db.query(BookModel).filter(
                    (BookModel.sale == False) | (BookModel.owner_id == user.id)
                ).all()
        else:
            # Guests see only unsold books
            books = db.query(BookModel).filter(BookModel.sale == False).all()

        # Collect the owner details for each book
        owner = []
        for book in books:
            owner.append(db.query(UserModel).filter(UserModel.id == book.owner_id).first())

        # Pair each book with its owner
        data = zip(books, owner)

        # Render the books page with the gathered data
        return templates.TemplateResponse("display_books.html", context={'request': request, 'data': data})

    except Exception as e:
        # In case of an error, respond with an HTTP exception
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Ensure the database session is closed after processing
        db.close()




@router.get('/creation/')
def creation_page(request: Request,user=Depends(login_manager)):
    """
    Display the book creation page.

    Parameters:
    request: Request object.
    user: Current user, obtained through dependency injection.

    Returns a TemplateResponse with 'create_book.html'.
    """
    return templates.TemplateResponse(
        "create_book.html",
        context={'request': request},
    )


@router.get('/modify/{ISBN}')
def ask_to_modify(ISBN: str, request: Request,user=Depends(login_manager)):
    """
    Display the modify book page for a specific book.

    Parameters:
    ISBN (str): ISBN of the book to modify.
    request: Request object.
    user: Current user, obtained through dependency injection.

    Returns a TemplateResponse with 'modify_book.html'.
    
    """
    # Start a new database session
    db = SessionLocal()
    
    book =  db.query(BookModel).filter(BookModel.ISBN == ISBN).first()
    
    return templates.TemplateResponse(
        "modify_book.html",
        context={'request': request, 'book': book}
    )


@router.post('/delete/{ISBN}')
def delete_book(ISBN: str, user=Depends(login_manager)):
    """
    Deletes a specific book from the database based on its ISBN. Only the book's owner or an admin can delete it.

    Parameters:
    - ISBN (str): The ISBN of the book to be deleted.
    - user: The current user, obtained through dependency injection with the login manager.

    If the book is not found, or if the user is neither the owner nor an admin, an HTTPException is raised.
    Returns a RedirectResponse to the '/all_books' page after deletion.
    """

    # Start a new database session
    db = SessionLocal()
    try:
        # Query for the book to be deleted
        book = db.query(BookModel).filter(BookModel.ISBN == ISBN).first()

        if not book:
            # If no book is found with the given ISBN, raise a 404 error
            raise HTTPException(status_code=404, detail="No book found with this ISBN.")

        if book.owner_id != user.id and user.group != "admin":
            # If the current user is neither the owner nor an admin, raise a 403 error
            raise HTTPException(status_code=403, detail="Not authorized to delete this book")

        # If checks pass, delete the book from the database
        db.delete(book)
        db.commit()
    except Exception as e:
        # In case of any error, rollback the transaction and raise an HTTPException
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Ensure the database session is closed after processing
        db.close()

    # Redirect to the 'all_books' page after successful deletion
    return RedirectResponse(url="/all_books", status_code=302)
