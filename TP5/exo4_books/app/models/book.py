from typing import Optional

from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy import String, Float, Integer, ForeignKey, Boolean
from app.database import Base
from app.models.users import User

class Book(Base):
    """
    A class representing a book in the database.

    Attributes
    ----------
    ISBN : str
        The International Standard Book Number, serves as the primary key.
    title : str
        The title of the book.
    author : str
        The author of the book.
    editor : str
        The editor of the book.
    price : float
        The price of the book.
    sale : bool
        A flag to indicate if the book is sold or not. Default is False.
    owner_id : str
        The identifier of the user who owns the book, as a foreign key.
    owner : User
        The relationship to the User model, representing the owner of the book.

    Notes
    -----
    - The 'books' table is defined with '__tablename__'.
    - Relationships are defined with SQLAlchemy ORM to link to the User model.
    """

    __tablename__ = "Books"

    ISBN = mapped_column(String(72), primary_key=True)
    title = mapped_column(String(72))
    author = mapped_column(String(72))
    editor = mapped_column(String(72))
    price = mapped_column(Float)
    sale = mapped_column(Boolean, default=False)
    owner_id = mapped_column(String(72), ForeignKey('users.id'))
    owner = relationship("User", back_populates="books")
