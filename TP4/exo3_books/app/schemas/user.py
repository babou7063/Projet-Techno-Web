from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    """
    A class representing a User.

    Attributes
    ----------
    first_name : str
        The first name of the user.
    last_name : str
        The last name of the user.
    email: EmailStr
        The email of the user.
    password: str
        The password of the user.
    status: str
        The status of the user (client / admin).

    Notes
    -----
    This class inherits from pydantic.BaseModel and uses the pydantic.Field class for validation.
    """
    id:str
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str
    password: str
    status: Optional[str] = None