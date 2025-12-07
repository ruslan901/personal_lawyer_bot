FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаём .env шаблон (без токенов)
RUN echo "BOT_TOKEN=your_bot_token_here" > .env && \
    echo "LAWYER_ID=854258933" >> .env && \
    echo "YOOMONEY_WALLET=your_wallet" >> .env

EXPOSE 8080

CMD ["python", "main.py"]
