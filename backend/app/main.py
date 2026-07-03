from fastapi import FastAPI

app = FastAPI(title="Log Dog API")

@app.get("/")
def read_root():
    return {"message": "Log Dog API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

