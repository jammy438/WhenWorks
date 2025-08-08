from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db

init_db()  # Initialize the database and create tables
#importing routes
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.events import router as events_router
from app.api.routes.users import router as users_router
from app.api.routes.shared import router as shared_router


app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(shared_router, prefix="/sharing", tags=["sharing"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Allows React (port 3002) to call FastAPI (port 8000) - as browsers block cross-origin requests by default
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3002"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
