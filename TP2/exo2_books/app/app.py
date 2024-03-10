from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
#from fastapi.staticfiles import StaticFiles
from app.routes.books import router as book_router

app = FastAPI(title="Books")
app.include_router(book_router)
#app.mount("/static", StaticFiles(directory="app/static"))
templates = Jinja2Templates(directory="templates")

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
