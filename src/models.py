# -*- coding: utf-8 -*-
"""

Put your atom models here


"""
import json
import math
import collections
from atom.api import *
from enamlnative.core.api import AsyncHttpClient
from enamlnative.core.app import BridgedApplication
from datetime import datetime
from client import Thermostat
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.defer import DeferredList
from utils import Model, State
#from pprint import pprint


class Theme(Model):
    name = Unicode()
    bg = Unicode("#eee")
    bg_light = Unicode("#f8f8f8")
    card = Unicode("#fff")
    text = Unicode("#333")
    text_light = Unicode("#999")
    icon = Unicode("#004981")
    drawer = Unicode("#d63a5f")


class Weather(Model):
    #: Loading
    loading_current = Bool()
    loading_forecast = Bool()

    #: Needs a refresh
    outdated = Bool(True)

    #: Weather fetching settings
    url = Unicode("https://api.openweathermap.org/data/2.5/{mode}"
                  "?units=metric&zip={zip}&appid={key}")
    client = Instance(AsyncHttpClient, ()).tag(persist=False)
    api_key = Unicode("9a225bbabfc3ef64bcbf023c4b5359b9")
    location = Unicode("18092")

    #: Map weather icons ID to an Icon
    icons = Dict(default={
        200: {'icon': 'wi_storm_showers',
              'label': 'thunderstorm with light rain'},
        201: {'icon': 'wi_storm_showers', 'label': 'thunderstorm with rain'},
        202: {'icon': 'wi_storm_showers',
              'label': 'thunderstorm with heavy rain'},
        210: {'icon': 'wi_storm_showers', 'label': 'light thunderstorm'},
        211: {'icon': 'wi_thunderstorm', 'label': 'thunderstorm'},
        212: {'icon': 'wi_thunderstorm', 'label': 'heavy thunderstorm'},
        221: {'icon': 'wi_thunderstorm', 'label': 'ragged thunderstorm'},
        230: {'icon': 'wi_storm_showers',
              'label': 'thunderstorm with light drizzle'},
        231: {'icon': 'wi_storm_showers',
              'label': 'thunderstorm with drizzle'},
        232: {'icon': 'wi_storm_showers',
              'label': 'thunderstorm with heavy drizzle'},
        300: {'icon': 'wi_sprinkle', 'label': 'light intensity drizzle'},
        301: {'icon': 'wi_sprinkle', 'label': 'drizzle'},
        302: {'icon': 'wi_sprinkle', 'label': 'heavy intensity drizzle'},
        310: {'icon': 'wi_sprinkle', 'label': 'light intensity drizzle rain'},
        311: {'icon': 'wi_sprinkle', 'label': 'drizzle rain'},
        312: {'icon': 'wi_sprinkle', 'label': 'heavy intensity drizzle rain'},
        313: {'icon': 'wi_sprinkle', 'label': 'shower rain and drizzle'},
        314: {'icon': 'wi_sprinkle', 'label': 'heavy shower rain and drizzle'},
        321: {'icon': 'wi_sprinkle', 'label': 'shower drizzle'},
        500: {'icon': 'wi_rain', 'label': 'light rain'},
        501: {'icon': 'wi_rain', 'label': 'moderate rain'},
        502: {'icon': 'wi_rain', 'label': 'heavy intensity rain'},
        503: {'icon': 'wi_rain', 'label': 'very heavy rain'},
        504: {'icon': 'wi_rain', 'label': 'extreme rain'},
        511: {'icon': 'wi_rain_mix', 'label': 'freezing rain'},
        520: {'icon': 'wi_showers', 'label': 'light intensity shower rain'},
        521: {'icon': 'wi_showers', 'label': 'shower rain'},
        522: {'icon': 'wi_showers', 'label': 'heavy intensity shower rain'},
        531: {'icon': 'wi_showers', 'label': 'ragged shower rain'},
        600: {'icon': 'wi_snow', 'label': 'light snow'},
        601: {'icon': 'wi_snow', 'label': 'snow'},
        602: {'icon': 'wi_snow', 'label': 'heavy snow'},
        611: {'icon': 'wi_sleet', 'label': 'sleet'},
        612: {'icon': 'wi_sleet', 'label': 'shower sleet'},
        615: {'icon': 'wi_rain_mix', 'label': 'light rain and snow'},
        616: {'icon': 'wi_rain_mix', 'label': 'rain and snow'},
        620: {'icon': 'wi_rain_mix', 'label': 'light shower snow'},
        621: {'icon': 'wi_rain_mix', 'label': 'shower snow'},
        622: {'icon': 'wi_rain_mix', 'label': 'heavy shower snow'},
        701: {'icon': 'wi_sprinkle', 'label': 'mist'},
        711: {'icon': 'wi_smoke', 'label': 'smoke'},
        721: {'icon': 'wi_day_haze', 'label': 'haze'},
        731: {'icon': 'wi_cloudy_gusts', 'label': 'sand, dust whirls'},
        741: {'icon': 'wi_fog', 'label': 'fog'},
        751: {'icon': 'wi_cloudy_gusts', 'label': 'sand'},
        761: {'icon': 'wi_dust', 'label': 'dust'},
        762: {'icon': 'wi_smog', 'label': 'volcanic ash'},
        771: {'icon': 'wi_day_windy', 'label': 'squalls'},
        781: {'icon': 'wi_tornado', 'label': 'tornado'},
        800: {'icon': 'wi_day_sunny', 'label': 'clear sky'},
        801: {'icon': 'wi_cloudy', 'label': 'few clouds'},
        802: {'icon': 'wi_cloudy', 'label': 'scattered clouds'},
        803: {'icon': 'wi_cloudy', 'label': 'broken clouds'},
        804: {'icon': 'wi_cloudy', 'label': 'overcast clouds'},
        900: {'icon': 'wi_tornado', 'label': 'tornado'},
        901: {'icon': 'wi_hurricane', 'label': 'tropical storm'},
        902: {'icon': 'wi_hurricane', 'label': 'hurricane'},
        903: {'icon': 'wi_snowflake_cold', 'label': 'cold'},
        904: {'icon': 'wi_hot', 'label': 'hot'},
        905: {'icon': 'wi_windy', 'label': 'windy'},
        906: {'icon': 'wi_hail', 'label': 'hail'},
        951: {'icon': 'wi_day_sunny', 'label': 'calm'},
        952: {'icon': 'wi_cloudy_gusts', 'label': 'light breeze'},
        953: {'icon': 'wi_cloudy_gusts', 'label': 'gentle breeze'},
        954: {'icon': 'wi_cloudy_gusts', 'label': 'moderate breeze'},
        955: {'icon': 'wi_cloudy_gusts', 'label': 'fresh breeze'},
        956: {'icon': 'wi_cloudy_gusts', 'label': 'strong breeze'},
        957: {'icon': 'wi_cloudy_gusts', 'label': 'high wind, near gale'},
        958: {'icon': 'wi_cloudy_gusts', 'label': 'gale'},
        959: {'icon': 'wi_cloudy_gusts', 'label': 'severe gale'},
        960: {'icon': 'wi_thunderstorm', 'label': 'storm'},
        961: {'icon': 'wi_thunderstorm', 'label': 'violent storm'},
        962: {'icon': 'wi_cloudy_gusts', 'label': 'hurricane'}
    })

    #: Current weather data
    current = Dict()

    #: Forecast data
    forecast = Dict()

    #: Forecast for every 3 hours
    hourly_forecast = List()

    #: Forecast for each day
    daily_forecast = List()

    def _observe_outdated(self, change):
        if self.outdated:
            self.load()

    def load(self):
        #: Fetch current
        self.loading_current = True
        url = self.url.format(mode="weather",
                              zip=self.location,
                              key=self.api_key)
        print("Fetching {}".format(url))
        self.client.fetch(url).then(self.on_load_current)

        #: Fetch forecast
        self.loading_forecast = True
        url = self.url.format(mode="forecast",
                              zip=self.location,
                              key=self.api_key)
        print("Fetching {}".format(url))
        self.client.fetch(url).then(self.on_load_forecast)

    def on_load_current(self, response):
        if not response.ok:
            return

        #: Source data
        current = json.loads(response.body)
        print("Current:")
        print(current)
        #: Make sure it's good before saving it

        for k in ['name', 'main', 'weather', 'wind']:
            if k not in current:
                print("Current weather response is invalid: "
                      "{}".format(current))
                #: Required key is missing, something is not right
                return

        self.current = current
        self.outdated = False
        self.loading_current = False

    def on_load_forecast(self, response):
        if not response.ok:
            return
            #: Source data
        forecast = json.loads(response.body)
        print("Forecast:")
        print(forecast)
        #: Make sure it's good before saving it
        valid = True
        if 'list' not in forecast:
            valid = False
        for item in forecast.get('list', []):
            if 'weather' not in item:
                valid = False
                break
        if not valid:
            print("Forecast weather response is invalid: "
                  "{}".format(forecast))
            #: Required key is missing, something is not right
            return

        self.forecast = forecast
        #print("Forecast:")
        #pprint(self.forecast)

        #: Update hourly
        self.hourly_forecast = self.forecast['list'][:9]

        #: Update daily
        daily_forecast = {}
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        daily_forecast[0] = [self.current]
        for item in self.forecast['list']:
            #: Item is 3 hour period
            date = datetime.fromtimestamp(item['dt'])

            #: Put in correct index
            dd = math.floor((date-today).total_seconds()/(60*60*24.0))
            if dd not in daily_forecast:
                daily_forecast[dd] = []
            daily_forecast[dd].append(item)

        self.daily_forecast = [daily_forecast[k]
                               for k in sorted(daily_forecast.keys())]

        self.outdated = False
        self.loading_forecast = False


class DateTime(Model):
    """ A model for a date so we can observe each
    value to update the ui whenever a certain
    value changes (ex every hour). Use date.now.strftime()
    to get whatever textual values needed.
    """
    now = Instance(datetime)

    #: Date fields any of these can be observed
    year = Int()
    day = Int()
    month = Int()
    hour = Int()
    minute = Int()
    second = Int()

    def __init__(self, *args, **kwargs):
        #: When default is requested, trigger
        #: an async loop to keep updating the time
        self._refresh_time()

    def _observe_now(self, change):
        """ Whenever now is changed, update all the fields """
        now = self.now
        self.year = now.year
        self.day = now.day
        self.hour = now.hour
        self.minute = now.minute
        self.second = now.second

    def _refresh_time(self):
        self.now = datetime.now()
        #: Update every second
        app = BridgedApplication.instance()
        app.timed_call(1000, self._refresh_time)


class AppState(State):
    #: Thermostat state
    current_temp = Float(30)  # in C
    current_humidity = Float(51)

    connected = Bool(True)

    #: Updates every second
    time = Instance(DateTime, ()).tag(persist=False)
    time_mode = Enum('12', '24')

    #: Weather results
    weather = Instance(Weather, ()).tag(persist=False)

    #: Fireplace state
    fireplace = Bool()
    has_fireplace = Bool()

    #: Themes
    themes = List(Theme, default=[
        Theme(name="Light"),
        Theme(name="Dark", bg="#333", bg_light="#484848", card="#555",
              drawer="#004981", text="#fff", text_light="#ccc"),
    ])
    theme = Instance(Theme)

    #: Pinout
    thermostat = Instance(Thermostat).tag(persist=False)
    address = Unicode("192.168.1.101:8888")
    addresses = List()
    connection = Instance(object).tag(persist=False)

    #: Settings
    set_temp = Float(28)  # in C
    system_mode = Enum('off', 'heat', 'cool', 'auto')
    units = Enum('imperial', 'metric')
    hysteresis = Float()
    developer_mode = Bool(True)

    #: TODO: Should be on the actual thermostat!
    temp_history = ContainerList(float)
    humidity_history = ContainerList(float)
    heat_history = ContainerList()
    cool_history = ContainerList()

    #: Messages
    messages = Instance(collections.deque, ()).tag(persist=False)
    message_count = Int().tag(persist=False)

    #: Page in
    current_screen = Int().tag(persist=False)

    def _default_theme(self):
        return self.themes[0]

    @observe('time.hour')
    def _update_weather(self, change):
        """ Update weather every hour """
        self.weather.load()

    def _default_thermostat(self):
        try:
            host, port = self.address.split(":")
        except ValueError:
            host, port = "192.168.1.101:8888".split(":")
        t = Thermostat()
        t.listener = self._on_message
        self.connection = reactor.connectTCP(str(host), int(port), t)
        return t

    def _observe_address(self, change):
        """ When the address changes reset the thermostat """
        if change['type'] != 'update':
            return
        if self.connection:
            try:
                self.connection.loseConnection()
            except Exception as e:
                print(e)
        self.thermostat = self._default_thermostat()

    def _on_message(self, change):
        """ Watch thermostat messages """
        #print("Thermostat update: {}".format(change))
        if change not in self.messages:
            self.messages.append(change)
            self.message_count += 1

    def find_thermostats(self):
        """ Scan the subnet to find all the thermostats or anything serving
        on the port 8888
        
        """
        ip, port = self.address.split(':')
        subnet = ip.split(".")[0:2]
        ds = []
        for i in range(255):
            point = TCP4ClientEndpoint(reactor, ".".join(subnet+[i]), port)
            d = connectProtocol(point, Protocol())
            d.addTimeout(1, reactor)
            ds.append(d)

        def on_results(results):
            addrs = []
            for i, result in enumerate(results):
                success, p = result
                if success:
                    addrs.append("{}:{}".format(
                            ".".join(subnet+[i]), port))
                    p.transport.loseConnection()
            self.addresses = addrs

        DeferredList(ds, consumeErrors=True).addCallback(on_results)

