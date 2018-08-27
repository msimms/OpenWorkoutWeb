# Copyright 2018 Michael J Simms

from sklearn.cluster import KMeans

class SensorAnalyzer(object):
    """Class for performing calculations on basic sensor information (heart rate, power, etc.)."""

    def __init__(self):
        super(SensorAnalyzer, self).__init__()
        self.start_time = None
        self.max = 0.0 # Maximum sensor value
        self.avg = 0.0 # Average sensor value
        self.sum = 0.0 # Used in computing the average
        self.readings = [] # All the readings

    def update_maximum_value(self, reading):
        """Computes the maximum value for the workout. Called by 'append_sensor_reading'."""
        if reading > self.max:
            self.max = reading

    def update_average_value(self, reading):
        """Computes the average value for the workout. Called by 'append_sensor_reading'."""
        self.sum = self.sum + reading
        num_readings = len(self.readings)
        if num_readings > 0:
            self.avg = self.sum / num_readings

    def append_sensor_reading(self, date_time, reading):
        """Adds another reading to the analyzer."""
        if self.start_time is None:
            self.start_time = date_time

        self.readings.append(reading)
        self.update_maximum_value(reading)
        self.update_average_value(reading)
