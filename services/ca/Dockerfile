FROM missfire

ADD . /usr/src/ca/

WORKDIR /usr/src/ca/ca

EXPOSE 80

# -u -- python with unbuffered output option
ENTRYPOINT ["python"]
CMD ["-u", "api.py"]
