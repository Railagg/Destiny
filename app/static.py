from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# Добавь это в main.py после создания app

# Создаем папку для статических файлов
os.makedirs("static", exist_ok=True)

# Раздаем статические файлы
app.mount("/fronted", StaticFiles(directory="fronted", html=True), name="fronted")
