FROM python:2.7.14-slim-jessie
MAINTAINER Tetiana Yarygina

# Install openssl
# Important: works with OpenSSL 1.0.2*, but not 1.1.0f
# To check the current OpenSSL version:
# RUN apt-cache policy openssl
RUN apt-get update && apt-get install openssl && \
    rm -rf /var/cache/apk/*

ADD . /requirements
RUN pip install -r /requirements/requirements.txt