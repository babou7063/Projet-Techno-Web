from pydantic import BaseModel, Field

class Book(BaseModel):
    """
    A class representing a book creation.

    Attributes
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book.
    title : str
        The title of the book.
    author: str
        author of the book
    editor: str
        editor of the book

    Notes
    -----
    This class inherits from pydantic.BaseModel and uses the pydantic.Field class for validation.
    """

    ISBN: str = Field(min_length=17)
    title: str
    author: str
    editor: str





