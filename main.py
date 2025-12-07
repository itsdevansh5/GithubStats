from fastapi import *
app=FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Github Stats API"}
