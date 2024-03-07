from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.books import router as book_router

app = FastAPI(title="Books")
app.include_router(book_router)
app.mount("/static", StaticFiles(directory="static"))

@app.on_event('startup')
def on_startup():
    print("Server started.")


def on_shutdown():
    print("Bye bye!")

