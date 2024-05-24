from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from projet.login_manager import login_manager 
from projet import models, schemas
from projet.database import SessionLocal
from fastapi import BackgroundTasks
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
def post_article(
    article: schemas.ArticleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_manager)

):
    db_article = models.Article(**article.dict(), author_id=user.id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    # Get subscribers
    subscriptions = db.query(models.Subscription).filter_by(author_id=user.id).all()
    subscriber_emails = [subscription.user.email for subscription in subscriptions]
    
    # Send email to subscribers
   

    message = MessageSchema(
        subject="New Article Posted",
        recipients=subscriber_emails,
        body=f"Hi, {user.first_name} {user.last_name} has posted a new article titled '{db_article.title}'. Check it out!",
        subtype="html"
    )

    fm = FastMail(ConnectionConfig(
    MAIL_USERNAME ="projetjournal91@gmail.com",
    MAIL_PASSWORD = "mvrfdvklfrlvnetz",
    MAIL_FROM = "projetjournal91@gmail.com",
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True))

    background_tasks.add_task(fm.send_message,message)

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

@router.get("/like/{article_id}")
def like_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).get(article_id)
    
    article.likes += 1
    db.commit()
    db.refresh(article)
    
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer)
    return {"status": "success", "dislikes": article.dislikes}

@router.get("/dislike/{article_id}")
def dislike_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).get(article_id)
    
    article.dislikes += 1
    db.commit()
    db.refresh(article)
    
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer)
    return {"status": "success", "dislikes": article.dislikes}