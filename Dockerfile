# Basic setup
FROM alpine:edge

# Metadata
MAINTAINER Kuribohrn "87871320+Kuribohrn@users.noreply.github.com"

# Commands
# Update systme-wide dependencies
RUN apk update

# Add Alpine testing repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing/" >> /etc/apk/repositories

# Update all repositories
RUN apk update

# Install git and pypy3
RUN apk add git pypy3

# Add and switch to bot user
RUN addgroup -S bot && adduser -S bot -G bot
USER bot

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# Ensure local pypy3 is preferred over distribution pypy3, and ensure pip is in path
ENV PATH /usr/lib/pypy/bin:/home/bot/.local/bin:$PATH

# Ensure pip is installed and latest
RUN pypy3 -m ensurepip
RUN pypy3 -m pip install --upgrade pip

# Clone project from repo
RUN git clone https://github.com/b01lers/b01lers-bot /home/bot/b01lers-bot
WORKDIR /home/bot/b01lers-bot

# Install project dependencies and run!
RUN pip install -r requirements.txt
RUN pypy3 main.py
