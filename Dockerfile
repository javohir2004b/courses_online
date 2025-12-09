FROM ubuntu:latest
LABEL authors="javohir"

ENTRYPOINT ["top", "-b"]