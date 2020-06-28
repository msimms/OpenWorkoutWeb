FROM ubuntu:18.04
RUN apt-get update && apt-get install -y sudo
EXPOSE 8080

COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install -r requirements.txt
COPY . /opt/app
