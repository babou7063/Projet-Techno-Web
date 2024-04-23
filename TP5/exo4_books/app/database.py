
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine(
    "sqlite:///data/db.sqlite",  # Path to the database file
    echo=True,  # Show generated SQL code in the terminal
)
SessionLocal = sessionmaker(engine)


class Base(DeclarativeBase):
    pass

from app.models.book import Book
from app.models.users import User


def create_database():
    Base.metadata.create_all(engine)


def delete_database():
    Base.metadata.clear()
