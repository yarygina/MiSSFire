FROM python:2.7.14-alpine3.6

MAINTAINER tya

RUN apk update && \
	apk add musl-dev && \
    apk add gcc && \
    rm -rf /var/lib/apt/lists/*

ADD . /requirements
RUN pip install -r /requirements/requirements.txt