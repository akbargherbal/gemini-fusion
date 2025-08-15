from fastapi import FastAPI

app = FastAPI(title="Gemini Fusion")

@app.get("/")
def read_root():
    return {"message": "Welcome to Gemini Fusion"}

# Future: Mount your routers here
# from routers import chat, conversations
# app.include_router(chat.router)
# app.include_router(conversations.router)