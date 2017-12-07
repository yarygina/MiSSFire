FROM tya1/missfire
MAINTAINER Tetiana Yarygina

ADD . /usr/src/apigateway/

WORKDIR /usr/src/apigateway/apigateway

EXPOSE 80

ENTRYPOINT ["python"]
CMD ["api.py"]

