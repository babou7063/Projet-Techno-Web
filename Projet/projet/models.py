from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from projet.database import Base
from datetime import datetime, timedelta


from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Subscription(Base):
    """
    A class representing a subscription.

    Attributes
    ----------
    user_id : str
        The ID of the user who subscribed.
    author_id : str
        The ID of the user who the user subscribed to.
    user : User
        The user who subscribed.
    author : User
        The user who the user subscribed to.
    """
    __tablename__ = 'subscriptions'
   
    user_id = Column(String(72), ForeignKey('users.id'), primary_key=True)
    author_id = Column(String(72), ForeignKey('users.id'), primary_key=True)
    user = relationship("User", foreign_keys=[user_id], back_populates="subscriptions")
    author = relationship("User", foreign_keys=[author_id], back_populates="subscribers")




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
    likes_dislikes_article = relationship("LikeDislikeArticle", back_populates="user")
    likes_dislikes_comment = relationship("LikeDislikeComments", back_populates="user")
    subscriptions = relationship("Subscription", foreign_keys=[Subscription.user_id], back_populates="user")
    subscribers = relationship("Subscription", foreign_keys=[Subscription.author_id], back_populates="author")


    
 

class Article(Base):
    """
    A class representing an article.

    Attributes
    ----------
    id : int
        Unique identifier for the article.
    body : str
        The content of the article.
    title : str
        The title of the article.
    created_at : datetime
        The date and time when the article was created.
    author_id : str
        The ID of the user who created the article.
    likes : int
        The number of likes for the article.
    dislikes : int
        The number of dislikes for the article.
    author : User
        The user who created the article.
    comments : list of Comment
        A list of comments associated with the article.
    likes_dislikes_article : list of LikeDislikeArticle
        A list of interactions associated with the article.
    """

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    body = Column(String, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
    author_id = Column(String(72), ForeignKey("users.id"))
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    author = relationship("User", back_populates="articles")
    comments = relationship("Comment", back_populates="article")
    likes_dislikes_article = relationship("LikeDislikeArticle", back_populates="article")

class Token(Base):
    """
    Used for resetting the password of a user.

    Attributes
    ----------
    token : str
        The token string.
    user_email : str
        The email of the user.
    user : User
        The user associated with the token.
    created_at : datetime
        The date and time when the token was created.
    expires_in : int
        The duration of the token in seconds.
    """
    __tablename__ = 'tokens'
    token = Column(String(72), primary_key=True)
    user_email = Column(String(72), ForeignKey('users.email'))
    user = relationship("User")
    created_at = Column(DateTime, server_default=func.now())
    expires_in = Column(Integer, default=3600)  # Durée en secondes

    def is_expired(self):
        """
        Check if the token has expired.

        Returns
        -------
        bool
            True if the token has expired, False otherwise.
        """
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
    created_at = Column(DateTime, server_default=func.now())
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    article = relationship("Article", back_populates="comments")
    author = relationship("User", back_populates="comments")
    likes_dislikes_comments = relationship("LikeDislikeComments", back_populates="comment")
    
    
class LikeDislikeArticle(Base):
    """
    A class representing an interaction (like/dislike) for an article.

    Attributes
    ----------
    id : int
        Unique identifier for the interaction.
    user_id : str
        The ID of the user who interacted with the article.
    article_id : int
        The ID of the article.
    is_like : bool
        If True, the user liked the article; if False, the user disliked the article.

    Relationships
    --------------
    user : User
        The user who interacted with the article.
    article : Article
        The article.
    """

    __tablename__ = "likes_dislikes_article"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(72), ForeignKey("users.id"))
    article_id = Column(Integer, ForeignKey("articles.id"))
    is_like = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="likes_dislikes_article")
    article = relationship("Article", back_populates="likes_dislikes_article")
    

class LikeDislikeComments(Base):
    """
    A class representing an interaction (like/dislike) for a comment.

    Attributes
    ----------
    id : int
        Unique identifier for the interaction.
    user_id : str
        The ID of the user who interacted with the comment.
    comment_id : int
        The ID of the comment.
    is_like : bool
        If True, the user liked the comment; if False, the user disliked the comment.

    Relationships
    --------------
    user : User
        The user who interacted with the comment.
    comment : Comment
        The comment.
    """

    __tablename__ = "likes_dislikes_comments"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(72), ForeignKey("users.id"))
    comment_id = Column(Integer, ForeignKey("comments.id"))
    is_like = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="likes_dislikes_comment")
    comment = relationship("Comment", back_populates="likes_dislikes_comments")

