FROM python:3.11-slim

WORKDIR /bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Этот порт не важен для бота, но Render требует
EXPOSE 10000

CMD python main.py
