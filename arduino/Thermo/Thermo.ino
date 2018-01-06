#if defined(ARDUINO)
SYSTEM_MODE(MANUAL);
#endif

#include <DHT.h>
#include <math.h>
#include <Member.h>
#include <RPCServer.h>
#include <ArduinoJson.h>

/* Modify the bellowing definitions for your AP/Router.*/
#define EEPROM_STATE_ADDR 0

class Thermostat: public RPCServer {
public:
	Thermostat(int port);

	Declare(Thermostat, getState, JsonObject&);
	Declare(Thermostat, setState, JsonObject&);
	void processSensors();
	void reconnectWifi();

protected:
	void loadState();
	void saveState();
	void configurePins();
	void bindObservers();
	void configureOutputs();

	// Handlers
	void onWifiChanged(JsonObject &change);
	void onTempChanged(JsonObject &change);
	void onFanChanged(JsonObject &change);
	void onLedChanged(JsonObject &change);
	void onFireplaceChanged(JsonObject &change);
	void onHeatChanged(JsonObject &change);
	void onCoolChanged(JsonObject &change);
	void onThermostatChanged(JsonObject &change);
	void onPinChanged(JsonObject &change);
	void onConfigChanged(JsonObject &change);

	void registerProcs() {
		Register(getState, JSON_RPC_RET_TYPE_OBJECT);
		Register(setState, JSON_RPC_RET_TYPE_OBJECT);
	}
private:
	// Pins
	Member(int,tempPin1,6);
	Member(int,tempPin2,7);
	Member(int,ledPin,13);
	Member(int,fanPin,9);
	Member(int,fireplacePin,10);
	Member(int,heatPin,11);
	Member(int,coolPin,12);

	Member(String,wifiSsid,String("ssid"));
  Member(String,wifiPass,String("password"));
  Member(String,wifiIp,String("0.0.0.0"));

	// Config
	Member(bool,tempSensor1Present,true);
	Member(bool,tempSensor2Present,false);
	Member(bool,fireplacePresent,false);
	Member(bool,heatPresent,true);
	Member(bool,coolPresent,true);
	Member(bool,fanPresent,true);
	Member(bool,configured,false);
	Member(String,heatMode,String("furnace")); // furnace, fireplace
	Member(String,fanMode,String("auto")); // off, auto
	Member(String,systemMode,String("off")); // off, cool, heat


	// State
	Member(bool,ledActive,false);
	Member(bool,fireplaceActive,false);
	Member(bool,fanActive,false);
	Member(bool,heatActive, false);
	Member(bool,coolActive,false);
	Member(float,hysteresisTemp,0.6);
	Member(float,desiredTemp,24.0);
	Member(float,insideTemp,0);  // in C
	Member(float,insideHumidity,0); // in %
	Member(float,outsideTemp,0); // in C
	Member(float,outsideHumidity,0); // in %


	// Helpers
	Member(String,version,String(__TIMESTAMP__)); // TODO: use this so clients know theyre in sync

	// Sensor stuff
	unsigned long lastUpdate;
	DHT tempSensors[2];

};

Thermostat::Thermostat(int port): RPCServer(port) {
	Thermostat &self = *(this);
	self.loadState();
	self.bindObservers();
	self.configurePins();
}

/**
 * Load persistent state from EEPROM
 */
void Thermostat::loadState() {
	Serial.println("Loading state...");
	StaticJsonBuffer<1024> jsonBuffer;
	char buf[1024];

	EEPROM.get(EEPROM_STATE_ADDR,buf);
	JsonObject &state = jsonBuffer.parse(buf);
	if (state.success()) {
		state["loading"] = true;
		setState(state);
		Serial.println("State loaded!");
	} else {
		Serial.println("State not loaded!");
	}
}

/**
 * Save persistent state to EEPROM
 */
void Thermostat::saveState() {
	Serial.println("Saving state...");

	char buf[1024];
	StaticJsonBuffer<2> jsonBuffer;
	JsonObject &state = getState(jsonBuffer.createObject());

	// Remove non-persistent properties
	state.remove("insideTemp");
	state.remove("outsideTemp");
	state.remove("insideHumidity");
	state.remove("outsideHumidity");
	state.remove("configured");
	state.remove("version");

	// Save buffer
	state.printTo(buf,state.measureLength()+1);
	EEPROM.put(EEPROM_STATE_ADDR,buf);
}


void Thermostat::configurePins() {
	Thermostat &self = *(this);

	tempSensors[0] = DHT(tempPin1,DHT22);
	tempSensors[1] = DHT(tempPin2,DHT22);

	// initialize the digital pin as an output
	pinMode(ledPin, OUTPUT);
	pinMode(fanPin, OUTPUT);
	pinMode(heatPin, OUTPUT);
	pinMode(coolPin, OUTPUT);
	pinMode(fireplacePin, OUTPUT);
	for (uint8_t i=0; i<2; i++) {
		tempSensors[i].begin();
	}

	self.configureOutputs();

	Serial.println("Pins configured");
}

/**
 * Make sure initial state matches the outputs
 */
void Thermostat::configureOutputs() {
	//ppass
}

/**
 * Set up property observers so the handlers
 * fire when one of the properties changes.
 */
void Thermostat::bindObservers() {

	MethodObserver<Thermostat> onFireplaceChanged(this, &Thermostat::onFireplaceChanged);
	fireplaceActive.observe(onFireplaceChanged);

	MethodObserver<Thermostat> onHeatChanged(this, &Thermostat::onHeatChanged);
	heatActive.observe(onHeatChanged);

	MethodObserver<Thermostat> onCoolChanged(this, &Thermostat::onCoolChanged);
	coolActive.observe(onCoolChanged);

	MethodObserver<Thermostat> onLedChanged(this, &Thermostat::onLedChanged);
	ledActive.observe(onLedChanged);
	fireplaceActive.observe(onLedChanged);

	MethodObserver<Thermostat> onFanChanged(this, &Thermostat::onFanChanged);
	fanActive.observe(onFanChanged);

	MethodObserver<Thermostat> onTempChanged(this, &Thermostat::onTempChanged);
	insideTemp.observe(onTempChanged);
	insideHumidity.observe(onTempChanged);
	outsideTemp.observe(onTempChanged);
	outsideHumidity.observe(onTempChanged);

	MethodObserver<Thermostat> onPinChanged(this, &Thermostat::onPinChanged);
	tempPin1.observe(onPinChanged);
	tempPin2.observe(onPinChanged);
	ledPin.observe(onPinChanged);
	fanPin.observe(onPinChanged);
	fireplacePin.observe(onPinChanged);
	heatPin.observe(onPinChanged);
	coolPin.observe(onPinChanged);

	MethodObserver<Thermostat> onConfigChanged(this, &Thermostat::onConfigChanged);
	configured.observe(onConfigChanged);
	systemMode.observe(onConfigChanged);
	fanMode.observe(onConfigChanged);
	fanPresent.observe(onConfigChanged);
	fireplacePresent.observe(onConfigChanged);
	heatPresent.observe(onConfigChanged);
	coolPresent.observe(onConfigChanged);
	heatMode.observe(onConfigChanged);
	desiredTemp.observe(onConfigChanged);
	tempSensor1Present.observe(onConfigChanged);
	tempSensor2Present.observe(onConfigChanged);


	MethodObserver<Thermostat> onThermostatChanged(this, &Thermostat::onThermostatChanged);
	fanMode.observe(onThermostatChanged);
	systemMode.observe(onThermostatChanged);
	insideTemp.observe(onThermostatChanged);
	desiredTemp.observe(onThermostatChanged);
	hysteresisTemp.observe(onThermostatChanged);
	fanPresent.observe(onThermostatChanged);
	fireplacePresent.observe(onThermostatChanged);
	heatPresent.observe(onThermostatChanged);
	coolPresent.observe(onThermostatChanged);
	heatMode.observe(onThermostatChanged);

	MethodObserver<Thermostat> onWifiChanged(this, &Thermostat::onWifiChanged);
	wifiSsid.observe(onWifiChanged);
	wifiPass.observe(onWifiChanged);

	Serial.println("Observers bound");
}

/**
 * When config changes,
 * @observe("fireplacePresent","coolPresent","ledPin","fanPin",
 * 					"fireplacePin","heatPin","coolPin","desiredTemp")
 */
void Thermostat::onConfigChanged(JsonObject &change) {
	Serial.println("onConfigChanged");
	//saveState();
	notifyAll(change);
}

/**
 * When the fan state changes, set the pin.
 * @observe("fanActive")
 */
void Thermostat::onWifiChanged(JsonObject &change) {
	Serial.println("onWifiChanged");
	reconnectWifi();
	notifyAll(change);
}

void Thermostat::reconnectWifi() {
    char addr[16];
    Serial.println("Reconnecting to wifi...\n");
    WiFi.off();
    delay(100);
    WiFi.on();
    String SSID = wifiSsid;
    String PASS = wifiPass;
    WiFi.setCredentials(SSID, PASS, WPA2, WLAN_CIPHER_AES);
    WiFi.connect();

    Serial.println("Waiting for an IP address...\n");
    while (!WiFi.ready()) {
        delay(1000);
    }

    // Wait IP address to be updated.
    IPAddress localIP = WiFi.localIP();
    while (localIP[0] == 0) {
  	  localIP = WiFi.localIP();
      delay(1000);
    }

    sprintf(addr, "%u.%u.%u.%u", localIP[0], localIP[1], localIP[2], localIP[3]);
    wifiIp = String(addr);
    Serial.println(addr);
}

/**
 * When pins change, reconfigure
 * @observe("tempPin1","tempPin2","ledPin","fanPin",
 * 					"fireplacePin","heatPin","coolPin")
 */
void Thermostat::onPinChanged(JsonObject &change) {
	Serial.println("onPinChanged");
	configurePins();
	notifyAll(change);
}

/**
 * When temp changes, notify the clients.xx
 * @observe("fanActive")
 */
void Thermostat::onTempChanged(JsonObject &change) {
	Serial.println("onTempChanged");
	if (isnan((float) change["old"]) && isnan((float) change["value"]) ) { // Ignore NaN
		// pass
	} else {
		notifyAll(change);
	}
}

/**
 * When the fan state changes, set the pin.
 * @observe("fanActive")
 */
void Thermostat::onFanChanged(JsonObject &change) {
	Serial.println("onFanChanged");
	digitalWrite(fanPin,(fanActive)? HIGH: LOW);
	notifyAll(change);
}

/**
 * When the led state changes, set the pin.
 * @observe("ledActive")
 */
void Thermostat::onLedChanged(JsonObject &change) {
	Serial.println("onLedChanged");
	digitalWrite(ledPin,(ledActive)? HIGH: LOW);
	notifyAll(change);
}

/**
 * When the fireplace state changes, set the pin.
 * @observe("fireplaceActive")
 */
void Thermostat::onFireplaceChanged(JsonObject &change) {
	Serial.println("onFireplaceChanged");
	digitalWrite(fireplacePin,(fireplaceActive)? HIGH: LOW);
	notifyAll(change);
}

/**
 * When the heater state changes, set the pin.
 * @observe("heatActive")
 */
void Thermostat::onHeatChanged(JsonObject &change) {
	//digitalWrite(fireplacePin.get(),(fireplaceActive.get())? HIGH: LOW);
	Serial.println("onHeatChanged");
	String mode = heatMode;
	if (mode.equals("furnace")) {
		digitalWrite(heatPin,(heatActive)? HIGH: LOW);
	} else if (mode.equals("fireplace")) {
		digitalWrite(heatPin,LOW);
		fireplaceActive = (bool) heatActive;
	}
	notifyAll(change);
}

/**
 * When the cool state changes, set the pin.
 * @observe("coolActive")
 */
void Thermostat::onCoolChanged(JsonObject &change) {
	//digitalWrite(fireplacePin.get(),(fireplaceActive.get())? HIGH: LOW);
	//fireplaceActive.set(heatActive.get());
	Serial.println("onCoolChanged");
	digitalWrite(coolPin,(coolActive)? HIGH: LOW);
	notifyAll(change);
}

/**
 * Set thermostat state based on temp readings.
 *
 * Triggered when one of the following changes
 *
 * @observe("systemMode","insideTemp","desiredTemp","hysteresisTemp")
 */
void Thermostat::onThermostatChanged(JsonObject &change) {
	Serial.println("onThermostatChanged");
	change.printTo(Serial);
	String mode = systemMode;
	if (mode.equals("heat")) {
		coolActive = false;
		if (insideTemp <= desiredTemp) {
			heatActive =true;
		} else if (insideTemp >= desiredTemp + hysteresisTemp) {
			heatActive = false;
		}
		// else leave as is
	} else if (mode.equals("cool")) {
		heatActive = false;
		if (insideTemp >= desiredTemp) {
			coolActive = true;
		} else if (insideTemp <= desiredTemp - hysteresisTemp) {
			coolActive = false;
		}
		// else leave as is
	} else {
		heatActive = false;
		coolActive = false;
	}
	Serial.println("~onThermostatChanged");
}

/**
 * Get current thermostat state.
 *
 * Keep it flat and simple stupid.
 */
JsonObject& Thermostat::getState(JsonObject &params) {
	Serial.println("Thermostat.getState");
	DynamicJsonBuffer buffer;
	JsonObject &state = buffer.createObject();

	state["tempPin1"] = (int)  tempPin1;
	state["tempPin2"] = (int)  tempPin2;
	state["ledPin"] = (int) ledPin;
	state ["fanPin"] = (int) fanPin;
	state ["fireplacePin"] = (int) fireplacePin;
	state["heatPin"] = (int) heatPin;
	state["coolPin"] = (int) coolPin;

	state["fireplacePresent"] = (bool) fireplacePresent;
	state["coolPresent"] = (bool) coolPresent;
	state["heatPresent"] = (bool) heatPresent;
	state["fanPresent"] = (bool) fanPresent;
	state["configured"] = (bool) configured;
	state["heatMode"] = (String) heatMode;
	state["fanMode"] = (String) fanMode;
	state["systemMode"] = (String) systemMode;

	state["ledActive"] = (bool) ledActive;
	state["fireplaceActive"] = (bool) fireplaceActive;
	state["fanActive"] = (bool) fanActive;
	state["heatActive"] = (bool) heatActive;
	state["coolActive"] = (bool) coolActive;
	state["hysteresisTemp"] = (float) hysteresisTemp;
	state["desiredTemp"] = (float) desiredTemp;
	state["insideTemp"] = (float) insideTemp;
	state["insideHumidity"] = (float) insideHumidity;
	state["outsideTemp"] = (float) outsideTemp;
	state["outsideHumidity"] = (float) outsideHumidity;

	// Wifi
	state["wifiSsid"] = (String) wifiSsid;
	state["wifiIp"] = (String) wifiIp;
	// password is write only!

	state["version"] = (String) version;

	return state;
}

/**
 * Configure the thermostat
 */
JsonObject& Thermostat::setState(JsonObject &params) {
	Serial.println("Thermostat.setState");
	// TODO: Don't repeat yourself like a flipping retard
	if (params.containsKey("tempPin1")) {
		tempPin1 = (int) params["tempPin1"];
	}

	if (params.containsKey("tempPin2")) {
		tempPin2 = (int) params["tempPin2"];
	}

	if (params.containsKey("ledPin")) {
		ledPin = (int) params["ledPin"];
	}

	if (params.containsKey("fanPin")) {
		fanPin = (int) params["fanPin"];
	}

	if (params.containsKey("fireplacePin")) {
		fireplacePin = (int) params["fireplacePin"];
	}

	if (params.containsKey("heatPin")) {
		heatPin = (int) params["heatPin"];
	}

	if (params.containsKey("coolPin")) {
		coolPin = (int) params["coolPin"];
	}

	if (params.containsKey("ledActive")) {
		ledActive = (bool) params["ledActive"];
	}

	if (params.containsKey("fanActive")) {
		fanActive = (bool) params["fanActive"];
	}

	if (params.containsKey("heatActive")) {
		heatActive = (bool) params["heatActive"];
	}

	if (params.containsKey("coolActive")) {
		coolActive = (bool) params["coolActive"];
	}

	if (params.containsKey("fireplaceActive")) {
		fireplaceActive = (bool) params["fireplaceActive"];
	}

	if (params.containsKey("hysteresisTemp")) {
		hysteresisTemp = (float) params["hysteresisTemp"];
	}

	if (params.containsKey("desiredTemp")) {
		desiredTemp = (float) params["desiredTemp"];
	}

	if (params.containsKey("systemMode")) {
		systemMode = String((const char*)params["systemMode"]);
	}

	if (params.containsKey("heatMode")) {
		heatMode = String((const char*)params["heatMode"]);
	}

	if (params.containsKey("fanMode")) {
		fanMode = String((const char*)params["fanMode"]);
	}

	if (params.containsKey("tempSensor1Present")) {
		tempSensor1Present = (bool) params["tempSensor1Present"];
	}
	if (params.containsKey("tempSensor2Present")) {
		tempSensor2Present = (bool) params["tempSensor2Present"];
	}

	if (params.containsKey("fanPresent")) {
		fanPresent = (bool) params["fanPresent"];
	}
	if (params.containsKey("fireplacePresent")) {
		fireplacePresent = (bool) params["fireplacePresent"];
	}
	if (params.containsKey("heatPresent")) {
		heatPresent = (bool) params["heatPresent"];
	}
	if (params.containsKey("coolPresent")) {
		coolPresent = (bool) params["coolPresent"];
	}

	if (params.containsKey("configured")) {
		configured = (bool) params["configured"];
	}

	if (params.containsKey("wifiSsid")) {
		wifiSsid = String((const char*)params["wifiSsid"]);
	}
	if (params.containsKey("wifiPass")) {
    wifiPass = String((const char*)params["wifiPass"]);
  }

	if (!params.containsKey("loading")) {
		saveState();
	}
	return getState(params);
}

void Thermostat::processSensors() {
	if (millis()-lastUpdate<2000) {
		return;
	}
	lastUpdate = millis();
	// Check sensor
	if (tempSensor1Present) {
		DHT &sensor1 = tempSensors[0];
		insideTemp = sensor1.getTempCelcius();
		insideHumidity = sensor1.getHumidity();
		//Serial.println("InsideTemp:");
		//Serial.println(insideTemp);
	}

	if (tempSensor2Present) {
		DHT &sensor2 = tempSensors[1];
		outsideTemp = sensor2.getTempCelcius();
		outsideHumidity = sensor2.getHumidity();
	}

}



// Start main code
Thermostat server(8888);

void setup() {
  // start up the serial interface
  Serial.begin(115200);
  Serial.println("Initializing JSON RPC server");

  // Setup wifi
  server.reconnectWifi();

  /* add setup code here */
  // Set number of clients
  server.setup(20,20);
  server.begin();
  Serial.println("Server started");
}

void loop() {
	// Handle RPC requests
	server.process();
	server.processSensors();

  // Sleep
  delay(10);

	// Ensure wifi is good
	if (!WiFi.ready()) {
	  // Should i just reset here??
	  System.reset();
	}
}
