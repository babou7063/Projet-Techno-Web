from typing import Optional

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
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
    """
    This function returns a database session using the `SessionLocal`
    from the `projet.database` module. The session is used to interact
    with the database.

    Yields:
        sqlalchemy.orm.session.Session: A database session.

    """
    # Create a new session using the `SessionLocal` from the `projet.database` module.
    db = SessionLocal()
    
    try:
        # Yield the session so that it can be used in the context of a with statement.
        yield db
    finally:
        # Close the session once the context is exited.
        db.close()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Returns the home page HTML response.

    Args:
        request (Request): The incoming request.

    Returns:
        HTMLResponse: The home page HTML response.
    """
    # Render the home.html template with the request context.
    return templates.TemplateResponse(
        "home.html",  # Template file path.
        context={'request': request}  # Template context data.
    )
    

@router.get("/write", response_class=HTMLResponse)
def write_article(request: Request, _user=Depends(login_manager)):
    """
    Returns the write article page HTML response.

    Args:
        request (Request): The incoming request.

    Returns:
        HTMLResponse: The write article page HTML response.
    """
    # Render the write_article.html template with the request context.
    return templates.TemplateResponse(
        "write_article.html",  # Template file path.
        context={'request': request}  # Template context data.
    )





@router.post("/post")
def post_article(
    article: schemas.ArticleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_manager)

):
    """
    Posts a new article to the database and sends an email to subscribers.

    Args:
        article (schemas.ArticleCreate): The article to be posted.
        background_tasks (BackgroundTasks): Background tasks to be executed.
        db (Session): The SQLAlchemy database session.
        user (models.User): The logged-in user.

    Returns:
        models.Article: The posted article.
    """
    # Create a new article and add it to the database
    db_article = models.Article(**article.dict(), author_id=user.id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    # Get subscribers
    subscriptions = db.query(models.Subscription).filter_by(author_id=user.id).all()
    subscriber_emails = [subscription.user.email for subscription in subscriptions]
    
    # Send email to subscribers
    
    # Create the email message
    message = MessageSchema(
        subject="New Article Posted",
        recipients=subscriber_emails,
        body=f"Hi, {user.first_name} {user.last_name} has posted a new article titled '{db_article.title}'. Check it out!",
        subtype="html"
    )

    # Create the FastMail instance
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

    # Add the send_message task to the background tasks
    background_tasks.add_task(fm.send_message,message)

    return db_article
    

async def get_optional_user(request: Request):
    try:
        user = await login_manager(request)
        return user
    except Exception:
        return None


@router.get("/read/{article_id}")
def read_article(request: Request, article_id: int, db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_optional_user)):
    """
    Retrieve an article from the database and its comments, and return the read article page.

    Args:
        request (Request): The incoming request.
        article_id (int): The ID of the article to retrieve.
        db (Session): The SQLAlchemy database session.

    Returns:
        TemplateResponse: The read article page HTML response.
    """
    # Retrieve the article from the database
    article = db.query(models.Article).get(article_id)
    
    # Retrieve the comments for the article
    article.comments = db.query(models.Comment).filter(models.Comment.article_id == article_id).all()

    # Render the read_article.html template with the request and article context
    return templates.TemplateResponse(
        "read_article.html",  # Template file path.
        context={
            'request': request,  # Template context data.
            'article': article,
            'user': user
        }
    )

@router.get("/search")
def search_article(request: Request, q: Optional[str]=None, db: Session = Depends(get_db)):
    """
    Search for articles based on the query string.

    Args:
        request (Request): The incoming request.
        q (Optional[str], optional): The query string. Defaults to None.
        db (Session, optional): The SQLAlchemy database session. Defaults to Depends(get_db).

    Returns:
        TemplateResponse: The search article page HTML response.
    """
    # Extract the query string
    query = q
    
    # If the query string is not None, split it into individual words
    if query is not None:
        queries = query.split()
        
        # Perform a search on the database for articles containing any of the words in the query string
        articles = db.query(models.Article).join(models.Article.author).filter(
            and_(*[
                or_(
                    models.Article.body.contains(query),
                    models.Article.title.contains(query),
                    models.User.first_name.contains(query),
                    models.User.last_name.contains(query)
                ) for query in queries
            ])
        )
    else:
        # If the query string is None, return an empty list of articles
        articles = []
    
    # Print the articles for debugging
    print(articles)
    
    # Render the search_article.html template with the request and articles context
    return templates.TemplateResponse(
        "search_article.html",
        context={
            'request': request,
            'articles': articles,
        }
    )

@router.get("/browse")
def search_article(request: Request, db: Session = Depends(get_db)):
    """
    Retrieve all articles from the database and return the browse article page.

    Args:
        request (Request): The incoming request.
        db (Session): The SQLAlchemy database session.

    Returns:
        TemplateResponse: The browse article page HTML response.
    """
    # Retrieve all articles from the database
    articles = db.query(models.Article).all()

    # Render the browse_article.html template with the request and articles context
    return templates.TemplateResponse(
        "browse_article.html",  # Template file path.
        context={
            'request': request,  # Template context data.
            'articles': articles
        }
    )
    

@router.get("/like/{article_id}")
def like_article(request: Request, article_id: int, user: models.User=Depends(login_manager), db: Session = Depends(get_db)):
    """
    Handle a like action for an article.

    Args:
        request (Request): The incoming request.
        article_id (int): The ID of the article to like.
        user (models.User): The user who is liking the article.
        db (Session): The SQLAlchemy database session.

    """
    # Retrieve the article from the database
    article = db.query(models.Article).get(article_id)
    
    # Check if the user has already interacted with the article
    check_interaction = db.query(models.LikeDislikeArticle).filter_by(article_id=article_id, user_id=user.id).first()
    
    if check_interaction:
        # If the user has already disliked the article
        if not check_interaction.is_like:
            # Update the interaction to like
            check_interaction.is_like = True
            # Update the like and dislike counts of the article
            article.likes += 1
            article.dislikes -= 1
    else:
        # If the user has not interacted with the article, create a new interaction and add a like
        new_interaction = models.LikeDislikeArticle(article_id=article_id, user_id=user.id, is_like=True)
        db.add(new_interaction)
        # Update the like count of the article
        article.likes += 1
        
    # Commit the changes to the database
    db.commit()
    # Refresh the article object to ensure latest values
    db.refresh(article)
    
    # Retrieve the referer from the request headers
    referer = request.headers.get("referer")
    # If there is a referer, return a redirect response to the referer
    if referer:
        return RedirectResponse(url=referer)
    # Otherwise, return a dictionary with the status and dislikes of the article
    return {"status": "success", "dislikes": article.dislikes}

@router.get("/dislike/{article_id}")
def dislike_article(request: Request, article_id: int, user: models.User=Depends(login_manager), db: Session = Depends(get_db)):
    """
    Handle a dislike action for an article.

    Args:
        request (Request): The incoming request.
        article_id (int): The ID of the article to dislike.
        user (models.User): The user who is disliking the article.
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary with the status and dislikes of the article.
    """
    # Retrieve the article from the database
    article = db.query(models.Article).get(article_id)
    
    # Check if the user has already interacted with the article
    check_interaction = db.query(models.LikeDislikeArticle).filter_by(article_id=article_id, user_id=user.id).first()

    if check_interaction:
        # If the user has already liked the article
        if check_interaction.is_like:
            # Update the interaction to dislike
            check_interaction.is_like = False
            # Update the like and dislike counts of the article
            article.likes -= 1
            article.dislikes += 1
    else:
        # If the user has not interacted with the article, create a new interaction and add a dislike
        new_interaction = models.LikeDislikeArticle(article_id=article_id, user_id=user.id, is_like=False)
        db.add(new_interaction)
        # Update the dislike count of the article
        article.dislikes += 1
        
    # Commit the changes to the database
    db.commit()
    # Refresh the article object to ensure latest values
    db.refresh(article)
    
    # Retrieve the referer from the request headers
    referer = request.headers.get("referer")
    # If there is a referer, return a redirect response to the referer
    if referer:
        return RedirectResponse(url=referer)
    # Otherwise, return a dictionary with the status and dislikes of the article
    return {"status": "success", "dislikes": article.dislikes}



@router.post("/add_comment/{article_id}")
def add_comment(
    article_id: int,  
    comment: str = Form(...),  
    user: models.User=Depends(login_manager), 
    db: Session = Depends(get_db) 
):
    """
    Add a comment to an article.

    Args:
        article_id (int): The ID of the article to add the comment to.
        comment (str): The content of the comment.
        user (models.User): The authenticated user.
        db (Session): The database session.

    Returns:
        dict: A dictionary with the status and the ID of the newly created comment.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You have to be connected")
        
    new_comment = models.Comment(
        body=comment,
        article_id=article_id,
        author_id=user.id,
        likes=0,
        dislikes=0
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {"status": "success", "comment_id": new_comment.id}

@router.get("/comments/like/{article_id}/{comment_id}")
def like_article(request: Request, article_id: int, comment_id: int, user: models.User=Depends(login_manager), db: Session = Depends(get_db)):
    """
    Handle a like action for a comment.

    Args:
        request (Request): The incoming request.
        article_id (int): The ID of the article that contains the comment.
        comment_id (int): The ID of the comment to like.
        user (models.User): The user who is liking the comment.
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary with the status and the number of likes on the comment.
    """
    # Retrieve the comment from the database
    comment = db.query(models.Comment).get(comment_id)
    
    # Check if the user has already interacted with the comment
    check_interaction = db.query(models.LikeDislikeComments).filter_by(comment_id=comment_id, user_id=user.id).first()
    
    if check_interaction:
        # If the user has already disliked the comment
        if not check_interaction.is_like:
            # Update the interaction to like
            check_interaction.is_like = True
            # Update the like and dislike counts of the comment
            comment.likes += 1
            comment.dislikes -= 1
    else:
        # If the user has not interacted with the comment, create a new interaction and add a like
        new_interaction = models.LikeDislikeComments(comment_id=comment_id, user_id=user.id, is_like=True)
        db.add(new_interaction)
        # Update the like count of the comment
        comment.likes += 1
        
    # Commit the changes to the database
    db.commit()
    # Refresh the comment object to ensure latest values
    db.refresh(comment)
    
    # Retrieve the referer from the request headers
    referer = request.headers.get("referer")
    # If there is a referer, return a redirect response to the referer
    if referer:
        return RedirectResponse(url=referer)
    # Otherwise, return a dictionary with the status and number of likes on the comment
    return {"status": "success", "likes": comment.likes}



@router.get("/comments/dislike/{article_id}/{comment_id}")
def dislike_comment(request: Request, comment_id: int, user: models.User=Depends(login_manager), db: Session = Depends(get_db)):
    """
    Handle a dislike action for a comment.

    Args:
        request (Request): The incoming request.
        comment_id (int): The ID of the comment to dislike.
        user (models.User): The user who is disliking the comment.
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary with the status and the number of dislikes on the comment.
    """
    # Retrieve the comment from the database
    comment = db.query(models.Comment).get(comment_id)

    # Check if the user has already interacted with the comment
    check_interaction = db.query(models.LikeDislikeComments).filter_by(comment_id=comment_id, user_id=user.id).first()

    if check_interaction:
        # If the user has already liked the comment
        if check_interaction.is_like:
            # Update the interaction to dislike
            check_interaction.is_like = False
            # Update the like and dislike counts of the comment
            comment.likes -= 1
            comment.dislikes += 1
    else:
        # If the user has not interacted with the comment, create a new interaction and add a dislike
        new_interaction = models.LikeDislikeComments(comment_id=comment_id, user_id=user.id, is_like=False)
        db.add(new_interaction)
        # Update the dislike count of the comment
        comment.dislikes += 1

    # Commit the changes to the database
    db.commit()
    # Refresh the comment object to ensure latest values
    db.refresh(comment)

    # Retrieve the referer from the request headers
    referer = request.headers.get("referer")
    # If there is a referer, return a redirect response to the referer
    if referer:
        return RedirectResponse(url=referer)
    # Otherwise, return a dictionary with the status and number of dislikes on the comment
    return {"status": "success", "dislikes": comment.dislikes}

    