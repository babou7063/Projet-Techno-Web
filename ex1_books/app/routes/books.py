
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.schemas.book import Book
import app.services.books as service

router = APIRouter(prefix="/books", tags=["Books"])


@router.get('/')
def get_all_books():
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
    return JSONResponse(
        content=[book.model_dump() for book in books],
        status_code=200,
    )

@router.get('/{ISBN}')
def get_book(ISBN: str):
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


@router.post('/')
def create_new_book(ISBN: str, title: str):
    """
    Create a new book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the new book.
    title : str
        The title of the new book.

    Returns
    -------
    JSONResponse
        A JSON response containing information about the newly created book.

    Raises
    ------
    HTTPException
        If the provided ISBN or title is invalid.

    """

    new_book_data = {
        "ISBN": ISBN,
        "title": title,
        
    }
    try:
        new_book = Book.model_validate(new_book_data)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ISBN or title is not valid.",
        )
    service.save_book(new_book)
    return JSONResponse(new_book.model_dump())


@router.post('/{ISBN}')
def modify_book(ISBN: str, title: str):
    """
    Modify an existing book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book to modify.
    title : str
        The new title for the book.

    Returns
    -------
    JSONResponse
        A JSON response containing information about the updated book.

    Raises
    ------
    HTTPException
        If the provided title is invalid or if the book with the provided ISBN is not found.

    """
    new_book_data = {
        "ISBN": ISBN,
        "title": title,
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

    return JSONResponse(updated_book)


@router.post('/delete/{ISBN}')
def delete_book(ISBN: str):
    """
    Delete an existing book entry.

    Parameters
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book to modify.
   
    Returns
    -------
    JSONResponse
        A JSON response saying the book has been deleted.

    Raises
    ------
    HTTPException
        If the book with the provided ISBN is not found.

    """
        
    
    book = service.delete_book_by_id(ISBN)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book found with this ISBN.",
        )

    return JSONResponse(book.model_dump())
       