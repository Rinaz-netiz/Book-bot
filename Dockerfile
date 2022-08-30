FROM python:3.10

WORKDIR /book_bot

ENV TELEGRAM_API_TOKEN=""

RUN pip install -U pip aiogram aiohttp beautifulsoup4 lxml && apt-get update
COPY *.py ./

ENTRYPOINT ["python", "server.py"]