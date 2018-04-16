1.0.0 - 2018/04/16:
--------------------
  * Smog-o-Meter 1.0
  * Add e-paper display
  * Use OTAA for LoRaWAN

0.9.0 - 2018/02/20:
--------------------
  * Measure data twice per hour (every 30 minutes)
  * Wait for 28 seconds with measurement to improve reliability

0.8.0 - 2018/01/28:
--------------------
  * Use LoRaWAN via TTN instead of WiFi
  * Remove RTC and persistence layer to send data after every measurement

0.7.0 - 2018/01/20:
--------------------
  * Move to a dedicated PCB
  * Battery voltage measurement not included yet

0.6.0 - 2018/01/18:
--------------------
  * Add external RTC module and bring back 10-minute granularity for influx data
  * Reorganize pin connections, almost all pins are now used...

0.5.1 - 2018/01/16:
--------------------
  * More LoPy4 issues: RTC state not kept when running on battery
  * Report data to influx the same way as to thingspeak, i.e. mean data from 6 consecutive
    measurements, with no timestamp
  * Temporarily removed RTC code that is not needed as we don't send timestamps

0.5.0 - 2018/01/16:
--------------------
  * Update for LoPy4: change PMS5003 pins because old ones are partially used by LoRa chip
  * Remove LED PWM code (temporarily?) beacuse LoPy4 crashed there...
  * Sleep for 598 seconds because 595 was a bit too short

0.4.1 - 2017/12/07:
--------------------
  * Fix reading datapoints from file
  * Fix computing mean datapoint
  * Use wake by button to enable debug mode (enable WiFi and exit)
  * Sleep for 595 seconds (5s to compensate for boot-up time)

0.4.0: Send data to Thingspeak using MQTT and measure outside T/RH
--------------------
  * send hourly mean data (average of last 6 measurements) - this is mainly to learn how
    MQTT works, it's suboptimal and it should use REST API and send batched updates with
    multiple measurements
  * Add DataPoint class that gathers all measurements and has adapters for influx and
    thingspeak formats
  * Move keys to keychain.py that's outside the repository

0.3.0: Button to trigger sending all available data
--------------------

0.2.2: Keep data file locally until it has been successfully posted
--------------------
	* also add LED flashing for storing data, sending data and failing to send data
	* disable expansion board LED during deep sleep
	* move Watchdog to boot.py

0.2.1: Resync RTC every time when connecting to WLAN
--------------------

0.2.0: Gather data every 10 minutes, but send every hour
--------------------
  * Store measurements data in a text file on flash
  * Once 5 measurements are stored, after taking sixth one
    send all the data to influx and remove the file
  * WiFi is required before first ever measurement to set up RTC
    and every hour to send data to influx
  * Some helper data is stored in NVRAM - adjust boot.py to reset
    NVRAM and delete cached measurements on hard resets

0.1.7:
--------------------
  * clean up project file, move PMS code to PMS5003 class

0.1.6:
--------------------
  * install 700mAh battery and step-up circuit inside pycase

0.1.5:
--------------------
  * fix battery voltage calculation

0.1.4:
--------------------
  * read 5 AQI samples instead of 10 (no. 2, 4, 6, 8 and 10)

0.1.3:
--------------------
  * disable printing with timestamp

0.1.2:
--------------------
  * connect to WLAN and setup RTC in a thread after temperature/humidity measurement

0.1.1:
--------------------
  * measure temperature, humidity and voltage in a separate thread

0.1.0:
--------------------
  * AQI
  * temperature
  * relative humidity
  * battery voltage
  * measurement duration
