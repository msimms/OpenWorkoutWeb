# StraenWeb
Workout tracking website and companion to the Straen mobile app. This is very much a work-in-progress, and is being done as a spare-time project, so set your expectations appropriately.

## Rationale
Why develop a workout tracker when there are so many closed-source options available?

* I needed a companion website to the mobile app of the same name that I developed. I needed this to make the live tracking feature possible.
* Other workout trackers do not support strength-based exercises, such as pull-ups and push-ups (press-ups).
* I think users should have control over their own data and this is only possible with an open source application.
* There are some analytical ideas that I have that none of the major activity tracking websites perform.
* Education. For the experience in performing full-stack software development: dealing with website deployment and scalability, and security issues.

## Major Features
* Enables the live tracking feature of the Straen mobile app.
* Supports strength (lifting) activities as well as distance (aerobic) activities.

## Major Todos
* Support for strength-based activities (this is partially implemented).
* Activity export.
* Continuous scrolling for the activity feed.
* Import from other services.
* Better graphics.
* Replace Google Maps with Open Street Map.
* Equipment tracking.
* More analytics.

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

## Tech
This software uses two other source projects to work properly:

* [LibMath](https://github.com/msimms/LibMath) - A collection of math utilities, including a peak finding algorithm.
* [fullcalendar](https://fullcalendar.io/) - A Javascript calendar implementation.

The app is written in a combination of Python and JavaScript.

## Social
Twitter: [@StraenApp](https://twitter.com/StraenApp)

## How To
For instructional material, consult the [Wiki](https://github.com/msimms/StraenWeb/wiki)

## License
Currently proprietary (though there are some source files that are under the MIT license). However I am considering moving the source code to either an MIT or MPL license.
