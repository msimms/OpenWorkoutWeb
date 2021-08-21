# Base images.
FROM ubuntu:18.04
RUN apt-get update && apt-get install -y sudo

# Make the service available on port 8080 within the Docker internal network.
EXPOSE 8080

# Copy the application into the image.
RUN mkdir -p /OpenWorkoutWeb
WORKDIR /OpenWorkoutWeb

# Install all of the python packages that we need.
RUN apt-get install -y python python-setuptools python-pip
RUN pip install -r requirements.txt

# Copy the rest of our application.
COPY . .

# Run the application.
CMD python2 start_flask.py --config openworkout.config
