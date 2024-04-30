from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from projet.database import engine
from projet.models import Base
from projet.routes import articles,users
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router=articles.router)
app.include_router(router=users.router)
templates = Jinja2Templates(directory="projet/templates")
app.mount("/static", StaticFiles(directory="../Projet/static"),name='static')

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        context={'request': request}
    )



@app.on_event('startup')
def on_startup():
    print("Server started.")


def on_shutdown():
    print("Bye bye!")


@app.exception_handler(400)
def custom_400(request, exception):
    return templates.TemplateResponse(
        "400_page.html",
        context={
            'request': request,
            'exception': exception
        },
        status_code=400,
    )
@app.exception_handler(401)
def custom_401(request, exception):
    return templates.TemplateResponse(
        "401_page.html",
        context={
            'request': request,
            'exception': exception
        },
        status_code=401,
    )

@app.exception_handler(404)
def custom_404(request, exception):
    return templates.TemplateResponse(
        "404_page.html",
        context={
            'request': request,
            'exception': exception
        },
        status_code=404,
    )


@app.exception_handler(409)
def custom_409(request, exception):
    return templates.TemplateResponse(
        "409_page.html",
        context={
            'request': request,
            'exception': exception
        },
        status_code=409,
    )


@app.exception_handler(RequestValidationError)
def custom_422(request, exception):
    return templates.TemplateResponse(
        "422_page.html",
        context={
            'request': request,
            'exception': exception
        },
        status_code=422,
    )
