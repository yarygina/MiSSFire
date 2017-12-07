FROM tya1/missfire
MAINTAINER Tetiana Yarygina

ADD . /usr/src/transactions/

WORKDIR /usr/src/transactions/transactions/

EXPOSE 80

ENTRYPOINT ["python"]
CMD ["api.py"]