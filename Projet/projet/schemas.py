from typing import Union

from pydantic import BaseModel


class CommentBase(BaseModel):
    body: str


class CommentCreate(BaseModel):
    body: str


class Comment(CommentBase):
    id: int
    article_id: int
    author_id: str
    likes: int
    dislikes: int

    class Config:
        from_attributes = True


class LikeDislikeBase(BaseModel):
    user_id: str
    article_id: int
    is_like: bool


class LikeDislikeCreate(LikeDislikeBase):
    pass


class LikeDislike(LikeDislikeBase):
    id: int
        
class ArticleBase(BaseModel):
    body: str
    title: str
    # description: Union[str, None] = None


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    author_id: int
    likes: int
    dislikes: int
    comments: list[Comment] = []
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    articles: list[Article] = []
    comments: list[Comment] = []

    class Config:
        from_attributes = True

class EmailSchema(BaseModel):
    email: str
    