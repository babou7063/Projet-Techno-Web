import logging
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError
from fastapi.templating import Jinja2Templates
from app.schemas.book import Book
import app.services.books as service
from typing import Annotated
from fastapi import Depends
from app.login_manager import login_manager

router = APIRouter(tags=["Books"])
templates = Jinja2Templates(directory="templates")

@router.get('/')
def display_home_page(request: Request):
    return templates.TemplateResponse(
        "home_page.html",
        context={'request': request}
    )


@router.get('/all_books')
def get_all_books(request: Request,user=Depends(login_manager)):
    """
    Retrieve information about all books.

    Returns
    -------
    JSONResponse
        A JSON response containing information about all books.

    Raises
    ------
    HTTPException
        If there is an issue retrieving books or no books are found.
    """
    books = service.get_all_books()
    return templates.TemplateResponse("display_books.html", context={'request': request, 'books': books})

@router.get('/book/{ISBN}')
def get_book(ISBN: str,user=Depends(login_manager)):
    """
    Retrieve information about a specific book based on its ISBN.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book to retrieve.

    Returns
    -------
    JSONResponse
        A JSON response containing information about the requested book.

    Raises
    ------
    HTTPException
        If the book with the provided ISBN is not found.
    """
    book = service.get_book_by_id(ISBN)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book found with this ISBN.",
        )
    return JSONResponse(book.model_dump())


@router.post('/create_book/', response_class=RedirectResponse, status_code=status.HTTP_303_SEE_OTHER)
def create_new_book(ISBN: Annotated[str, Form()], title: Annotated[str, Form()],author: Annotated[str, Form()], editor: Annotated[str, Form()],user=Depends(login_manager)):
    """
    Create a new book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the new book.
    title : str
        The title of the new book.
    author: str
        author of the book
    editor: str
        editor of the book

    Returns
    -------
    Redirect the user to the list books pages

    Raises
    ------
    HTTPException
        If the provided ISBN or title is invalid.
    """
    new_book_data = {
        "ISBN": ISBN.strip(),
        "title": title.strip(),
        "author":author.strip(),
        "editor":editor.strip()
    }
    try:
        new_book = Book.model_validate(new_book_data)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ISBN or title.",
        )
    try:
        service.save_book(new_book)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with this ISBN already exists.",
        )
    return RedirectResponse("/all_books", status_code=status.HTTP_303_SEE_OTHER)

@router.get('/creation/')
def creation_page(request: Request,user=Depends(login_manager)):
    return templates.TemplateResponse(
        "create_book.html",
        context={'request': request},
    )


@router.get('/modify/{ISBN}')
def ask_to_modify(ISBN: str, request: Request,user=Depends(login_manager)):
    book = service.get_book_by_id(ISBN)
    
    return templates.TemplateResponse(
        "modify_book.html",
        context={'request': request, 'book': book}
    )


@router.post('/modify/{ISBN}')
def modify_book(ISBN: str, title: Annotated[str, Form()],author: Annotated[str, Form()], editor: Annotated[str, Form()],user=Depends(login_manager)):
    """
    Modify an existing book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book to modify.
    title : str
        The new title for the book.
    author: str
        author of the book
    editor: str
        editor of the book

    Returns
    -------
    JSONResponse
        A JSON response containing information about the updated book.

    Raises
    ------
    HTTPException
        If the provided title is invalid or if the book with the provided ISBN is not found.
    """
    bk = service.get_book_by_id(ISBN)

    new_book_data = {
        "ISBN": ISBN,
        "title": title,
        "author":author,
        "editor":editor
    }
    try:
        new_book = Book.model_validate(new_book_data)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title is not valid.",
        )
    
    updated_book = service.update_book(new_book)
    if updated_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book found with this ISBN.",
        )

    return RedirectResponse(url="/all_books", status_code=302)



@router.post('/delete/{ISBN}')
def delete_book(ISBN: str,request:Request,user=Depends(login_manager)):
    """
    Delete an existing book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book to modify.

    Returns
    -------
    Redirect the user to the list books pages

    Raises
    ------
    HTTPException
        If the book with the provided ISBN is not found.
    """
    if request.method == 'POST':
        book = service.delete_book_by_id(ISBN)
        if book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No book found with this ISBN.",
            )
        return RedirectResponse(url="/all_books", status_code=302)
