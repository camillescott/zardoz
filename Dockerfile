# syntax=docker/dockerfile:1
FROM gorialis/discord.py:3.8-alpine
LABEL zardoz_version="1.1.0"
MAINTAINER camillescott

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
RUN pip install .

RUN mkdir /logs /db
VOLUME /logs
VOLUME /db

ENV ZARDOZ_TOKEN SET_ZARDOZ_TOKEN_TO_YOUR_DISCORD_TOKEN
ENTRYPOINT ["zardoz", "bot", "--database-dir", "/db", "--log", "/logs/zardoz.log"]
