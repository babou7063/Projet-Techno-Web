from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base  

class User(Base):
    """
    A class representing a user.

    Attributes
    ----------
    id : str
        Unique identifier for the user.
    first_name : str
        The first name of the user.
    last_name : str
        The last name of the user.
    email : str
        The email address of the user. Must be unique.
    password : str
        The hashed password of the user.
    status : str
        The status of the user (active, blocked). Nullable.
    group : str
        The group to which the user belongs (admin, client). Nullable.
    books : list of Book
        A list of books associated with the user.

    Notes
    -----
    This class uses SQLAlchemy ORM for database interactions.
    """

    __tablename__ = 'users'

    id = Column(String(72), primary_key=True)
    first_name = Column(String(72))
    last_name = Column(String(72))
    email = Column(String(72), unique=True)
    password = Column(String(72))
    status = Column(String(2048), nullable=True)
    group = Column(String(2048), nullable=True)
    books = relationship("Book", back_populates="owner")
