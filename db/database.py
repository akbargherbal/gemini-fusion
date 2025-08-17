from sqlmodel import SQLModel, create_engine

# Define the database URL for our SQLite database file
DATABASE_URL = "sqlite:///gemini_fusion.db"

# Create the engine, the central point of contact with the database.
# The 'connect_args' is a specific requirement for using SQLite with FastAPI
# to allow the database to be accessed from multiple threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """
    Initializes the database by creating all tables defined by SQLModel metadata.
    This function will be called once on application startup.
    """
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created successfully.")