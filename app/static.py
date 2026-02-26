from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# Добавь это в main.py после создания app

# Создаем папку для статических файлов
os.makedirs("static", exist_ok=True)
os.makedirs("frontend", exist_ok=True)  # ✅ создаём папку frontend

# Раздаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Для корневого пути - отдаём index.html
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")
