# Copyright 2018 Michael J Simms

from sklearn.cluster import KMeans
import numpy
import Keys

class SensorAnalyzer(object):
    """Class for performing calculations on basic sensor information (heart rate, power, etc.)."""

    def __init__(self, sensor_type, units, activity_type):
        super(SensorAnalyzer, self).__init__()
        self.activity_type = activity_type
        self.type = sensor_type
        self.units = units
        self.start_time = None
        self.end_time = None
        self.max = 0.0 # Maximum sensor value
        self.avg = 0.0 # Average sensor value
        self.sum = 0.0 # Used in computing the average
        self.readings = [] # All the readings
        self.value_readings = [] # All the readings, just the value part
        self.num_readings = 0 # Cached for efficiency
        self.bests = {} # Best times within the current activity (best mile, best 20 minute power, etc.)

    def get_best_time(self, record_name):
        """Returns the time associated with the specified record, or None if not found."""
        if record_name in self.bests:
            return self.bests[record_name]
        return None

    def update_maximum_value(self, reading):
        """Computes the maximum value for the workout. Called by 'append_sensor_value'."""
        if reading > self.max:
            self.max = reading

    def update_average_value(self, reading):
        """Computes the average value for the workout. Called by 'append_sensor_value'."""
        self.sum = self.sum + reading
        if self.num_readings > 0:
            self.avg = self.sum / self.num_readings

    def append_sensor_value(self, date_time, value):
        """Adds another reading to the analyzer."""
        if self.start_time is None:
            self.start_time = date_time
        self.end_time = date_time

        self.num_readings = self.num_readings + 1
        self.readings.append([date_time, value])
        self.value_readings.append(value)
        self.update_maximum_value(value)
        self.update_average_value(value)

    def analyze(self):
        """Called when all sensor readings have been processed."""
        results = {}
#        if len(self.value_readings) > 0:
#            # Perform kmeans clustering.
#            np_readings = numpy.array(self.value_readings)
#            kmeans_analyzer = KMeans(n_clusters=4)
#            kmeans_analyzer.fit(np_readings.reshape(-1,1))
#            clusters = kmeans_analyzer.cluster_centers_
#            cluster_num = 1
#            for cluster in clusters:
#                key_str = self.type + " " + Keys.CLUSTER + " " + str(cluster_num)
#                value_str = "{:.2f}".format(cluster[0])
#                results[key_str] = value_str + " " + self.units
#                cluster_num = cluster_num + 1
        results.update(self.bests)
        return results
