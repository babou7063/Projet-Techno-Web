from pydantic import BaseModel, Field

class Book(BaseModel):
    """
    A class representing a book.

    Attributes
    ----------
    ISBN : str
        The ISBN (International Standard Book Number) of the book.
    title : str
        The title of the book.

    Notes
    -----
    This class inherits from pydantic.BaseModel and uses the pydantic.Field class for validation.
    """

    ISBN: str = Field(min_length=17)
    title: str
