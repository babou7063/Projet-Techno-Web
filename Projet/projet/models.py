from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from projet.database import Base
from datetime import datetime, timedelta


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
    is_active : Bool
        The status of the user (true-->active, false --> blocked). Nullable.
    group : str
        The group to which the user belongs (admin, client). Nullable.
    articles : list of Article
        A list of articles associated with the user.

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
    is_active = Column(Boolean, default=True)
    group = Column(String(2048), nullable=True)
    
    articles = relationship("Article", back_populates="author")
    comments = relationship("Comment", back_populates="author")
 

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    body = Column(String, index=True)
    title = Column(String, index=True)
    # description = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
    author_id = Column(Integer, ForeignKey("users.id"))
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    author = relationship("User", back_populates="articles")
    comments = relationship("Comment", back_populates="article")

class Token(Base):
    "used for reset the passeword of a user"
    __tablename__ = 'tokens'
    token = Column(String(72), primary_key=True)
    user_email = Column(Integer, ForeignKey('users.email'))
    user = relationship("User")
    created_at = Column(DateTime, server_default=func.now())
    expires_in = Column(Integer, default=3600)  # Durée en secondes

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.expires_in)
    
    
class Comment(Base):
    """
    A class representing a comment.

    Attributes
    ----------
    id : int
        Unique identifier for the comment.
    body : str
        The content of the comment.
    article_id : int
        The ID of the article to which the comment belongs.
    author_id : str
        The ID of the user who posted the comment.
    likes : int
        The number of likes for the comment.
    dislikes : int
        The number of dislikes for the comment.
    """

    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    body = Column(String, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    author_id = Column(String(72), ForeignKey("users.id"))
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    article = relationship("Article", back_populates="comments")
    author = relationship("User", back_populates="comments")