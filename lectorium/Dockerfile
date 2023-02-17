FROM --platform=linux/amd64 python:3.10-slim

LABEL MAINTAINER="Valery Makroguzov valera.nedbai@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PROJECT_DIR='/lectorium'
ENV ARCHITECTURE=x64

COPY ./src          $PROJECT_DIR
COPY ./Pipfile      $PROJECT_DIR
COPY ./Pipfile.lock $PROJECT_DIR

WORKDIR $PROJECT_DIR

RUN pip install  \
      --upgrade pip pipenv && pipenv install --system --deploy

RUN apt-get update && \
    apt-get -y install graphviz

ARG HOST
ARG PORT

ENV HOST=$HOST
ENV PORT=$PORT

EXPOSE $PORT
ENTRYPOINT uvicorn main:get_application --host $HOST --port $PORT
