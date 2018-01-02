FROM missfire

ADD . /usr/src/reversests/

WORKDIR /usr/src/reversests/reversests

EXPOSE 80

# -u -- python with unbuffered output option
ENTRYPOINT ["python"]
CMD ["-u", "api.py"]
