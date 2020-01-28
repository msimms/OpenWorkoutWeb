[![API Docs](https://img.shields.io/badge/api-raml-green.svg)](https://raw.githubusercontent.com/msimms/StraenWeb/master/api.raml)
[![API Docs](https://img.shields.io/badge/api-html-green.svg)](https://mikesimms.net/straen/api/api.html)

# StraenWeb
Workout tracking website and companion to the Straen mobile app. This is very much a work-in-progress, and is being done as a spare-time project, so set your expectations appropriately.

## Rationale
Why develop a workout tracker when there are so many closed-source options available?

* I needed a companion website to the mobile app of the same name that I developed. I needed this to make the live tracking feature possible.
* Other workout trackers do not support strength-based exercises, such as pull-ups and push-ups (press-ups).
* I think users should have control over their own data and this is only possible with an open source application.
* There are some analytical ideas that I have that none of the major activity tracking websites perform.
* I want to do some experiments with automatically generating workout plans. This will serve as the platform for this idea.
* Education. For the experience in performing full-stack software development: dealing with website deployment and scalability, and security issues.

## Origin of the Name
Straen is the Welsh word for stress and exercise is a (positive) form of stress. Also, it was the only thing I could think of where I could register a decent domain name.

## Major Features
* Enables the live tracking feature of the Straen mobile app.
* Supports strength (lifting) activities as well as distance (aerobic) activities.

## Major Todos
* Support for strength-based activities (this is partially implemented).
* Import from other services.
* Better graphics.
* Replace Google Maps with Open Street Map.
* Equipment tracking.
* More analytics.

[Full bug and feature tracking](https://github.com/msimms/StraenWeb/issues).

## Installation
To install the dependencies:
```
python setup.py
```

## Execution
The software is designed to work within multiple frameworks. Currently, cherrypy and flask are supported.

To run the web service under the cherrypy framework:
```
python start_cherrpy.py [--debug] [--host <hostname>] [--hostport <hostport>] [--googlemapskey <key>]
```

To run the web service under the flask framework:
```
python start_flask.py [--debug] [--host <hostname>] [--hostport <hostport>] [--googlemapskey <key>]
```

*If a Google Maps key is not provided, OpenStreetMap will be used instead.*

## Architecture

The software architecture makes it possible to use this system with different front-end technologies. Also, computationally expensive analysis tasks are kept separate from the main application, communicating via RabbitMQ.

![Architecture Diagram](https://github.com/msimms/StraenWeb/blob/master/docs/Architecture.png?raw=true)

## Version History

### 0.1
* Initial version. Application exhibits basic functionality: can login and view activities received from the iOS companion app.
* Live tracking is functional.

### 0.2
* Added the ability to update email address and password.
* Added the ability to delete one's account and all associated data.
* Added the ability to delete a single activity.
* Added an API for receiving location updates from the companion mobile app.
* Support for HTTPS.
* Many small bug fixes.

### 0.3
* Rudimentary support for lifting activities (pull-ups, push-ups, etc.).
* Support for tags.
* Support for comments.
* Allow activities to be public or private.
* Implemented basic user following.
* Many small bug fixes.

### 0.4
* Activity importing from TCX and GPX files.
* Beginnings of statistical analysis.
* Ability to switch between metric and imperial units.
* Code refactoring to support multiple frameworks (cherrypy and flask).

### 0.5
* Automated data analysis, i.e. an activity is automatically analyzed when the upload is complete or when it has been updated by the mobile application. The results are cached for efficiency.
* Automatic identification of different workout types, such as tempo and interval runs and bike rides.
* Better support for the flask web application framework.

### 0.6
* Ability to upload an entire directory.

### 0.6
* Ability to import an entire directory of files.
* Added a calendar view.
* Activity export.

### 0.7
* Added celery and rabbitmq to distribute analysis tasks.

### 0.8
* Results from distributed tasks are now written direclty to the database for efficiency purposes.
* File imports are now also distributed over rabbitmq and celery with the results being written directly to the database.

### 0.9
* API documentation in RAML.
* Added profile option for resting heart rate.
* Added VO2Max, BMI, and estimated FTP calculations.
* Beginnings of automated workout plan generation. Still plenty of work to do.

### 0.10
* Support for OpenStreetMaps (support for Google Maps is still available).
* Activity export in GPX format.
* Fetch six month records, to use as the basis for workout plan generation.

### 0.11
* Fixes to adding tags and gear to activities.
* Added cycling power distribution graph.
* Too many optimizations to list.
* Too many small bug fixes to list.
* Generation of feature list prior to automated workout plan generation.

### 0.12
* Updates to the flask front end.
* Updates to the OpenStreetMap option.

### 0.13
* Bug fixes.

### 0.14
* Bug fixes.

### 0.15
* Added gear tracking.
* Added location descriptions (i.e., Florida, United States).
* Importing data now also starts the analysis process.
* Bug fixes.

### 0.16
* Rudimentary run plan generation - still much to do.
* Updates to support python3.
* Bug fixes.

### 0.17
* Bug fixes when importing and exporting activities.
* Ability to export position data as a CSV file.
* Bug fixes in computing gear distances.

### 0.18
* Bug fixes.
* Added an iCal server for subscribing to planned workouts.

## Tech
This software uses several other source projects to work properly:

* [LibMath](https://github.com/msimms/LibMath) - A collection of math utilities, including a peak finding algorithm.
* [ZwoReader](https://github.com/msimms/ZwoReader) - A simple utility for parsing a ZWO-formatted file.
* [fullcalendar](https://fullcalendar.io/) - A Javascript calendar implementation.
* [chosen](https://github.com/harvesthq/chosen) - A select box implementation that is used for the tag user interface.
* [pymongo](https://github.com/mongodb/mongo-python-driver) - Python interface to mongodb.
* [flask](http://flask.pocoo.org) - A microframework for developing python-based web apps (optional).

The app is written in a combination of Python, HTML, and JavaScript.

## Social
Twitter: [@StraenApp](https://twitter.com/StraenApp)

## How To
For instructional material, consult the [Wiki](https://github.com/msimms/StraenWeb/wiki)

## License
Currently proprietary (though there are some source files that are under the MIT license). However I am considering moving the source code to either an MIT or MPL license.
