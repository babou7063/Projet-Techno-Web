from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, or_
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
def write_article(request: Request, _user=Depends(login_manager)):
    return templates.TemplateResponse(
        "write_article.html",
        context={'request': request}
    )


@router.post("/post")
def post_article(article: schemas.ArticleCreate, db: Session = Depends(get_db), user: models.User=Depends(login_manager)):
    db_article = models.Article(**article.model_dump(), author_id=user.id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.get("/read/{article_id}")
def read_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).get(article_id)
    return templates.TemplateResponse(
        "read_article.html",
        context={
            'request': request,
            'article': article,
        }
    )

@router.get("/search")
def search_article(request: Request, q: Optional[str]=None, db: Session = Depends(get_db)):
    query = q
    if query is not None:
        queries = query.split()
        articles = db.query(models.Article).join(models.Article.author).filter(and_(*[or_(
            models.Article.body.contains(query), 
            models.Article.title.contains(query),
            models.User.first_name.contains(query),
            models.User.last_name.contains(query),
        ) for query in queries]))
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

@router.get("/browse")
def search_article(request: Request, db: Session = Depends(get_db)):
    articles = db.query(models.Article).all()
    return templates.TemplateResponse(
        "browse_article.html",
        context={
            'request': request,
            'articles': articles,
        }
    )

