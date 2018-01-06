#include <ArduinoJson.h>
#include <Member.h>

class Model {
public:
	Model() {}
  
	void setup() {
		MethodObserver<Watcher> method(&foo, &Watcher::onCharChanged);
		  characterReceived.observe(method);
	}

	void onLastValueChanged(JsonObject &change) {
		Serial.println("Watch");
		change.printTo(Serial);
	}

	Member(char,lastValue,"a");
};

// This signal will be emitted when we process characters
Model demo();
void setup() {
  Serial.begin(9600);

  // Observe using a function
  FunctionObserver func(onCharChanged);
  demo.lastValue.observe(func);
}

void loop() {
  // Emit a characterReceived signal every time a character arrives on the serial port.
  while(Serial.available()) {
	char c = Serial.read();
	Serial.println(c);
    demo = c;
  }
}
