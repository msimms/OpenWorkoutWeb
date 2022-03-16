[![API Docs](https://img.shields.io/badge/api-raml-green.svg)](https://raw.githubusercontent.com/msimms/OpenWorkoutWeb/master/api.raml)
[![API Docs](https://img.shields.io/badge/api-html-green.svg)](https://raw.githubusercontent.com/msimms/OpenWorkoutWeb/master/api.html)
![](https://travis-ci.com/msimms/OpenWorkoutWeb.svg?branch=master)

# OpenWorkoutWeb
Workout tracking website and optional companion to the Open Workout mobile app. This is very much a work-in-progress and is being done as a spare-time project, so set your expectations appropriately.

## Rationale
Why develop a workout tracker when there are so many closed-source options available?

* I needed a companion website to the mobile app of the same name that I developed. I needed this to make the live tracking feature possible.
* Other workout trackers do not support strength-based exercises, such as pull-ups and push-ups (press-ups).
* I think users should have control over their own data and this is only possible with an open source application.
* There are some analytical ideas that I have which none of the major activity tracking websites perform.
* I want to do some experiments with automatically generating workout plans. This will serve as the platform for this idea.
* Education. For the experience in performing full-stack software development: dealing with website deployment and scalability, and security issues.

## Major Features
* Enables the live tracking feature of the Open Workout mobile app.
* Supports strength (lifting) activities as well as distance (aerobic) activities.

## Major Todos
* Support for strength-based activities (this is partially implemented).
* Import from other services.
* Better graphics.
* Replace Google Maps with Open Street Map.
* More analytics.

[Full bug and feature tracking](https://github.com/msimms/OpenWorkoutWeb/issues).

## Installation
1. Clone the source code:
```
git clone https://github.com/msimms/OpenWorkoutWeb
```

2. Install the python dependencies:
```
cd OpenWorkoutWeb
python setup.py
```

3. Install other package dependencies, specifically `mongodb` and `rabbitmq`, which are services the application depends on:

```
#
# Example for macOS:
#

# Install mongod and start the service.
brew tap mongodb/brew
brew install mongodb-community@5.0
brew services start mongodb/brew/mongodb-community

# Install rabbitmq and start the service.
brew install rabbitmq
brew services restart rabbitmq
```

## Execution
The software is designed to work within multiple frameworks. Currently, cherrypy and flask are supported.
It is also designed to work with both python2 and python3.

To run the web service under the cherrypy framework:
```
python start_cherrypy.py --config openworkout.config
```

To run the web service under the flask framework:
```
python start_flask.py --config openworkout.config
```

*If a Google Maps key is not provided, OpenStreetMap will be used instead.*

## Architecture

The software architecture makes it possible to use this system with different front-end technologies. Also, computationally expensive analysis tasks are kept separate from the main application, communicating via RabbitMQ.

![Architecture Diagram](https://github.com/msimms/OpenWorkoutWeb/blob/master/docs/architecture/Architecture.png?raw=true)

## Workout Plans

This feature is very much under development and will go through several iterations before being ready for general use. The idea is to use the athlete's existing data to generate workouts to help in reaching future goals.

## User Guide

For instructional material, consult the [Wiki](https://github.com/msimms/OpenWorkoutWeb/wiki)

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
* Added gear tracking. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/4)
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
* Bug fixes, including many pertaining to the flask front end as well as activity analysis.
* Added an iCal server for subscribing to planned workouts.
* Added planned workouts to the My Activities calendar.

### 0.19
* Added a map that shows the countries, US states, and Canadian provinces in which activities were recorded. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/18)
* Bug fixes and performance improvements.

### 0.20
* Moved more functionality to the API.
* Display US and Canada together for state/province statistics as it just looks better.
* Reworked the follower/following system, so that everyone is just 'friends'.
* Track mile and kilometer split times. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/19)
* Bug fixes.

### 0.21
* Moved more functionality to the API.
* Moved distance and pace calculations to the front end (at least when using Google Maps). [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/20)
* Bug fixes.

### 0.22
* Bug fixes.

### 0.23
* Bug fixes. Includes python2 and python3 fixes for the activity analyzer as well as fixes to managing activity tags.

### 0.24
* Bug fixes and performance optimizations.
* More work on run workout plan generation.
* Added gear defaults. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/17)
* Display mile and kilometer split times. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/19)

### 0.25
* Ability to import FIT files. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/22)
* Ability to export workouts in ZWO fomrat. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/1)
* More work on run workout plan generation.

### 0.26
* Replaced command line options with a configuration file. [Feature Page](https://github.com/msimms/OpenWorkoutWeb/issues/24)
* More work on run workout plan generation.

### 0.27
* Bug fixes and performance optimizations.
* More work on run workout plan generation.
* Added the ability to retire gear.

### 0.28
* Bug fixes with respect to python3.
* Added a 404 page for the cherrypy front end.
* More work on run workout plan generation.

### 0.29
* Bug fixes.
* Work towards saving photos.
* Now saving the final that was uploaded and not just the data that was extracted from it.
* More work on run workout plan generation.

### 0.30
* Bug fixes and performance optimizations.
* Moved more logic to the client.
* More work on run workout plan generation, specifically updating the scheduler.

### 0.31
* Bug fixes.
* Minor UI updates.

### 0.32
* Bug fixes and performance optimizations.
* Minor UI updates.
* Ability to upload photo upload.

### 0.33
* Bug fixes and performance optimizations.

### 0.34
* Bug fixes and performance optimizations.
* Minor UI updates.
* Ability to synchronize with the mobile app (i.e. receive activities that we don't already have).
* More API work.

### 0.35
* Bug fixes and performance optimizations.
* Added pace plan synchronization with the mobile app.
* More API work.

### 0.36
* Bug fixes and performance optimizations.
* Fixed planned workout synchronization with the mobile app.
* Fixed heart rate zone generation.

### 0.37
* Bug fixes and performance optimizations.

### 0.38
* Bug fixes and performance optimizations, specifically on activity deletion and when loading the activities calendar view.

### 0.38
* Bug fixes and performance optimizations, including a lot of graph fixes.
* Initial cut of csv import functionality.

### 0.39
* Bug fixes and performance optimizations.

### 0.40
* Bug fixes and performance optimizations.

### 0.41
* Project renamed.
* Bug fixes and performance optimizations.
* Temperature data is now shown.
* Pool swimming workouts can now be imported.
* Default gear can now be specified.
* Bug fixes to personal record tracking.
* Style fixes.

### 0.42
* Bug fixes and performance optimizations.

### 0.43
* Bug fixes and performance optimizations.
* Added support for browser dark mode.
* Added the ability to edit gear names.

### 0.44
* Bug fixes and performance optimizations.
* Added a race calendar, to replace manually specifying goals.

### 0.45
* Bug fixes.

### 0.46
* Bug fixes.
* Analysis service now scans for unanalyzed activities.

## Tech
This software uses several other source projects to work properly:

* [LibMath](https://github.com/msimms/LibMath) - A collection of math utilities, including a peak finding algorithm.
* [ZwoReader](https://github.com/msimms/ZwoReader) - A simple utility for parsing a ZWO-formatted file.
* [fullcalendar](https://fullcalendar.io/) - A Javascript calendar implementation.
* [chosen](https://github.com/harvesthq/chosen) - A select box implementation that is used for the tag user interface.
* [pymongo](https://github.com/mongodb/mongo-python-driver) - Python interface to mongodb.
* [cherrypy](https://cherrypy.github.io/) - A framework for python-based web apps (optional).
* [flask](http://flask.pocoo.org) - A microframework for python-based web apps (optional).
* [python-fitparse](https://github.com/dtcooper/python-fitparse) - A library for parsing .FIT files.

The app is written in a combination of Python, HTML, and JavaScript.

## Social
Twitter: [@OpenWorkoutApp](https://twitter.com/OpenWorkoutApp)

## License
Currently proprietary (though many of the source files are under the MIT license). However I am considering moving the remainder of the source code to either an MIT or MPL license.
