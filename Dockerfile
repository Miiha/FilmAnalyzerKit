FROM miiha/python-opencv-ffmpeg

WORKDIR /usr/src/app
RUN mkdir -p /usr/src/app

COPY . /usr/src/app

ENV PBR_VERSION 1.0.0

RUN echo "deb http://ftp.debian.org/debian wheezy main"  >> /etc/apt/sources.list && \
    echo "deb-src http://ftp.debian.org/debian wheezy main" >> /etc/apt/sources.list && \
    apt-get -yqq update && \
    apt-get install -y build-essential ghostscript && \
    make init && \
    make install  && \
    touch /usr/local/lib/python3.5/site-packages/.env

CMD /bin/bash

