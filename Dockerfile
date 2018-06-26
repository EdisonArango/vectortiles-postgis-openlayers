FROM python:2.7
RUN mkdir /config
ADD requirements.txt /config/
RUN pip install -r /config/requirements.txt

ENV FLASK_APP=/src/app.py
ENV FLASK_DEBUG=1

ADD ./src /src
WORKDIR /src