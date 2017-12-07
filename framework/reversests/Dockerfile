FROM debian:jessie
MAINTAINER Tetiana Yarygina

ADD . /usr/src/reversests/

WORKDIR /usr/src/reversests/reversests

EXPOSE 80

RUN apt-get update && apt-get upgrade -y && apt-get install -y openssl

# -u -- python with unbuffered output option
ENTRYPOINT ["python"]
CMD ["-u", "api.py"]
