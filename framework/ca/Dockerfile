FROM debian:jessie
MAINTAINER Tetiana Yarygina

ADD . /usr/src/ca/

WORKDIR /usr/src/ca/ca

EXPOSE 80

RUN apt-get update && apt-get upgrade -y && apt-get install -y openssl

# -u -- python with unbuffered output option
ENTRYPOINT ["python"]
CMD ["-u", "api.py"]
