from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from projet.database import engine
from projet.models import Base
from projet.routes import articles

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router=articles.router)
templates = Jinja2Templates(directory="projet/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        context={'request': request}
    )