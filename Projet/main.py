import uvicorn
import projet.models as model
 
from projet.database import engine


def createdatabase():
    model.Base.metadata.create_all(engine)



if __name__ == '__main__':
    createdatabase()
    uvicorn.run("projet.app:app", log_level="info", port=8000)