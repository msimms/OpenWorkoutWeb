# Base images.
FROM ubuntu:18.04
RUN apt-get update && apt-get install -y sudo

# Make the service available on port 8080.
EXPOSE 8080

# Install all of the python packages that we need.
COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install -r requirements.txt
COPY . /opt/app
