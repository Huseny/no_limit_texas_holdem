from fastapi import FastAPI
from app.api import hands
from fastapi.middleware.cors import CORSMiddleware


origins = ["http://localhost:3000"]

app = FastAPI(
    title="Texas Hold'em Poker Backend",
    version="1.0.0",
    description="A backend service for managing Texas Hold'em Poker games.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hands.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Poker Backend API"}
