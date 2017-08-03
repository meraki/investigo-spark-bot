#FROM python:2.7-onbuild
#https://github.com/docker-library/python/blob/7663560df7547e69d13b1b548675502f4e0917d1/2.7/onbuild/Dockerfile

FROM python:2.7

RUN mkdir -p /usr/src
WORKDIR /usr/src

COPY . /usr/src
RUN pip install --no-cache-dir -r requirements.txt