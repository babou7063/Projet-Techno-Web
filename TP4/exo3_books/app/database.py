from datetime import date
from uuid import uuid4

database = {
    "books": {
        "978-2-84049-755-4": {
            "ISBN": "978-2-84049-755-4",
            "title" : "Ecstasy and me",
            "author" : "vanderkoof",
            "editor" : "EECI",
        },
        "978-2-84009-755-4": {
            "ISBN": "978-2-84009-755-4",
            "title": "Ecstasy and you",
            "author" : "Woomkerf",
            "editor" : "ACMI",
        },
    },

    "users": [
        
          {  "id": str(uuid4()),
            "first_name":"ulrich",
            "last_name": "naurel",
            "email": "ulrich90@gmail.com",
            "password": "john_password",
            "statut" : "client"
        },

    ],
}
