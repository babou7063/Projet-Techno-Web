import uvicorn


if __name__ == '__main__':
    uvicorn.run("projet.app:app", log_level="info", port=8000)
