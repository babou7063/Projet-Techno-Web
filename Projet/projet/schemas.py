from typing import Union

from pydantic import BaseModel


class ArticleBase(BaseModel):
    body: str
    # title: str
    # description: Union[str, None] = None


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    author_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    articles: list[Article] = []

    class Config:
        orm_mode = True