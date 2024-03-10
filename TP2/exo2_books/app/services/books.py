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

    Raises
    ------
    ValueError
        If the book already exists
    """
    if new_book.ISBN in database["books"]:
        raise ValueError(f"Book {new_book.ISBN} already exists")
    database["books"][new_book.ISBN] = new_book.model_dump()
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
    books = [Book.model_validate(book) for book in books_data.values()]
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

    try:
        selected_book = database["books"][ISBN]
    except KeyError:
        return None
    selected_book = Book.model_validate(selected_book)
    return selected_book
    
def delete_book_by_id(ISBN: str) -> Book | None:
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
    try:
        deleted_book = database["books"].pop(ISBN)
    except KeyError:
        return None
    deleted_book = Book.model_validate(deleted_book)
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
    database["books"][new_book.ISBN]["title"] = new_book.title
    return new_book
