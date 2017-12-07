FROM tya1/missfire
MAINTAINER Tetiana Yarygina

ADD . /usr/src/payment/

WORKDIR /usr/src/payment/payment/

EXPOSE 80

ENTRYPOINT ["python"]
CMD ["api.py"]