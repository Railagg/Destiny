from fastapi import FastAPI

app = FastAPI(title="Destiny Game API")

@app.get("/")
def root():
    return {
        "message": "Destiny API is working!",
        "status": "ok"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
