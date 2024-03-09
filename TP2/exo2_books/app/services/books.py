from app.schemas.book import Book
from app.database import database


def save_book(new_book: Book) -> Book:
    """
    Save a new book to the database.

    Parameters
    ----------
    new_book : Book
        The book object to be saved.

    Returns
    -------
    new_book : Book
        The saved book object.

    """
    database["books"].append(new_book.model_dump())
    return new_book


def get_all_books() -> list[Book]:
    """
    Retrieve all books from the database.

    Returns
    -------
    books : List
        List of all books in the database.

    """
    books_data = database["books"]
    books = [Book.model_validate(data) for data in books_data]
    return books


def get_book_by_id(ISBN: str) -> Book | None:
    """
    Retrieve a book from the database based on its ISBN.

    Parameters
    ----------
    ISBN : str
        ISBN of the book to be retrieved.

    Returns
    -------
    selected_book | None
        The retrieved book object or None if not found.

    """

    print(database)
    selected_book = [
        book for book in database["books"]
        if book["ISBN"] == ISBN
    ]
    if len(selected_book) < 1:
        return None
    selected_book = Book.model_validate(selected_book[0])
    return selected_book
    
def delete_book_by_id(ISBN: str) -> dict | None:
    """
    Delete a book from the database based on its ISBN.

    Parameters
    ----------
    ISBN : str
        ISBN of the book to be deleted.

    Returns
    -------
    deleted_book | None
        The deleted book object or None if not found.

    """
    deleted_book = None
    for idx, book in enumerate(database["books"]):
        if book["ISBN"] == ISBN:
            deleted_book = Book.model_validate(book)
            database["books"].pop(idx)
    return deleted_book
    
def update_book(new_book: Book) -> Book | None:
    """
    Update a book in the database with new information.

    Parameters
    ----------
    new_book : Book
        The updated book object.

    Returns
    -------
    new_book | None
        The updated book object or None if the book to be updated doesn't exist.

    """
    modify_book = get_book_by_id(new_book.ISBN)
    
    if modify_book is None:
        return modify_book
    
    else :
        for book in database['books']:
            if book["ISBN"] == new_book.ISBN:
                book["title"] = new_book.title
                return book
