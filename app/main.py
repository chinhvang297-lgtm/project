# /Users/shanzi/iemsProject/app/main.py
import uvicorn
from fastapi import FastAPI
from app.api import routes
from app.db.session import init_db

init_db()

app = FastAPI(title="NBA Prediction Agent System")

app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "NBA Agent System is Running! 🏀"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)