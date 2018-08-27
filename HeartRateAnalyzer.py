# Copyright 2018 Michael J Simms

class HeartRateAnalyzer(object):
    """Class for performing calculations on heart rate data."""

    def __init__(self):
        super(HeartRateAnalyzer, self).__init__()
        self.start_time = None
        self.max_hr = 0.0 # Maximum HR (in bpm)
        self.avg_hr = 0.0 # Average HR (in bpm)
        self.hr_sum = 0.0 # Used in computing the average
        self.num_readings = 0 # Used in computing the average

    def update_maximum_hr(self, reading):
        """Computers the maximum HR for the workout. Called by 'append_sensor_reading'."""
        if reading > self.max_hr:
            self.max_hr = reading

    def update_average_hr(self, reading):
        """Computers the average HR for the workout. Called by 'append_sensor_reading'."""
        self.hr_sum = self.hr_sum + reading
        if self.num_readings > 0:
            self.avg_hr = self.hr_sum / self.num_readings

    def append_sensor_reading(self, date_time, reading):
        """Adds another reading to the analyzer."""

        if self.start_time is None:
            self.start_time = date_time

        self.num_readings = self.num_readings + 1
        self.update_maximum_hr(reading)
        self.update_average_hr(reading)
