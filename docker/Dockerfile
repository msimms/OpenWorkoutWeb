# Base images.
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y sudo

# Install python3.
RUN apt -y install python3
RUN apt -y install python3-pip

# Make the service available on port 8080 within the Docker internal network.
EXPOSE 8080

# Make a directory for the app.
RUN mkdir -p /OpenWorkoutWeb
WORKDIR /OpenWorkoutWeb

# Copy the app into the image.
COPY . .
RUN ls -la /OpenWorkoutWeb/*
RUN ls -la /*

# Install the python packages that we need.
RUN pip3 install -r /OpenWorkoutWeb/requirements.txt

# Run the application.
CMD python3 start_cherrypy_wsgi.py --config openworkout.config
