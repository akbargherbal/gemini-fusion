from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import the database initialization function and the routers
from db.database import create_db_and_tables
from routers import chat, conversations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Define startup and shutdown events for the application.
    """
    print("Application starting up...")
    # This function will create the database and tables if they don't exist
    create_db_and_tables()
    yield
    print("Application shutting down...")


# Create the main FastAPI application instance with the lifespan manager
app = FastAPI(title="Gemini Fusion", lifespan=lifespan)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main index.html template."""
    return templates.TemplateResponse("index.html", {"request": request})


# Include the API routers from the other files
app.include_router(chat.router)
app.include_router(conversations.router)