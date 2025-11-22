import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="FastAPI 基礎入門",
    description="這是一個 FastAPI 基礎入門的教學專案",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/", tags=["root"], summary="根路徑", description="這是一個根路徑的示例")
def read_root():
    return {"message": "Hello, FastAPI!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)