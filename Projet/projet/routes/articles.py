from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from projet.login_manager import login_manager 
from projet import models, schemas
from projet.database import SessionLocal

router = APIRouter(prefix="/articles",tags=["Articles"])
templates = Jinja2Templates(directory="projet/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        context={'request': request}
    )

@router.get("/write", response_class=HTMLResponse)
def write_article(request: Request,user=Depends(login_manager)):
    return templates.TemplateResponse(
        "write_article.html",
        context={'request': request}
    )


@router.post("/post")
def post_article(article: schemas.ArticleCreate, db: Session = Depends(get_db),user=Depends(login_manager)):
    user_id = 0 # FIXME: Add authentification
    db_article = models.Article(**article.model_dump(), author_id=user_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.get("/search")
def search_article(request: Request, q: Optional[str]=None, db: Session = Depends(get_db)):
    query = q
    if query is not None:
        articles = db.query(models.Article).filter(models.Article.body.contains(query))
    else:
        articles = []
    print(articles)
    return templates.TemplateResponse(
        "search_article.html",
        context={
            'request': request,
            'articles': articles,
        }
    )

