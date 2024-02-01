FROM python:3.12.0-alpine3.18
LABEL maintainer="imsintech@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
# COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# Copy everything in this directory to docker
COPY ./ /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    # apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache redis && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base \
        postgresql-dev \
        musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    # Use double square brackets for the conditional statement
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        telegram-user

ENV PATH="/py/bin:$PATH"

USER telegram-user