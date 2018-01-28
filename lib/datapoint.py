class DataPoint:

    __slots__ = ['pm10', 'pm25', 'temperature', 'humidity', 'voltage', 'duration', 'version', 'timestamp']

    def __init__(self, **kwargs):
        required = list(self.__slots__)
        for key, value in kwargs.items():
            setattr(self, key, value)
            required.remove(key)
        if len(required) > 0:
            raise ValueError


    def to_influx(self, include_timestamp=True):
        data = 'aqi,indoor=1,version={} pm25={},pm10={},temperature={},humidity={},voltage={},duration={}' \
            .format(self.version, self.pm25, self.pm10, self.temperature, self.humidity, \
            self.voltage, self.duration)
        if include_timestamp is True:
            data += ' {}000000000'.format(self.timestamp)
        return data


    def to_thingspeak(self):
        return 'field1={}&field2={}&field3={}&field4={}&field5={}&field6={}' \
            .format(self.pm10, self.pm25, self.temperature, self.humidity, self.voltage, \
            self.duration)


    def to_bytes(self):
        # pm10 [ug/m] - int - 2b
        # pm25 [ug/m] - int - 2b
        # temp [K] - int - 2b
        # humidity [%/10] - int - 2b
        # voltage (mv) - int - 2b
        # duration (ms) - int - 2b
        # version - str

        payload = b''
        payload += int(self.pm10).to_bytes(2, 'little')
        payload += int(self.pm25).to_bytes(2, 'little')
        temp_k = self.temperature + 273.15
        payload += int(temp_k*100).to_bytes(2, 'little')
        payload += int(self.humidity*100).to_bytes(2, 'little')
        payload += int(self.voltage).to_bytes(2, 'little')
        payload += int(self.duration).to_bytes(2, 'little')
        payload += self.version

        return payload


    @classmethod
    def mean(cls, datapoints):
        mean_pm10 = 0
        mean_pm25 = 0
        mean_temperature = 0
        mean_humidity = 0
        mean_duration = 0
        valid_temp_datapoints = 0

        for d in datapoints:
            mean_pm10 += d.pm10
            mean_pm25 += d.pm25
            mean_duration += d.duration
            if d.temperature is not -1:
                mean_temperature += d.temperature
                mean_humidity += d.humidity
                valid_temp_datapoints += 1

        return cls(
            pm10 = mean_pm10/len(datapoints),
            pm25 = mean_pm25/len(datapoints),
            temperature = -1 if valid_temp_datapoints == 0 else mean_temperature/valid_temp_datapoints,
            humidity = -1 if valid_temp_datapoints == 0 else mean_humidity/valid_temp_datapoints,
            duration = mean_duration/len(datapoints),
            voltage = datapoints[-1].voltage,
            version = datapoints[-1].version,
            timestamp = datapoints[-1].timestamp
        )
