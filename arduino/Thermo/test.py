import serial
import json

class Thermostat(serial.Serial):

    def query(self,cmd,raw=False):
        self.write(cmd if raw else json.dumps(cmd))
        r = self.read(1)
        assert r, "FAIL: NO RESPONSE"
        r = r+self.read(self.inWaiting())
        print r
        return json.loads(r)


def testStress():
    t = Thermostat('/dev/ttyACM0',115200)
    try:
        for i in range(100):
            t.query({'method':'toggleLed','params':{'status':True},'id':i})
            t.query({'method':'noid','params':{'status':False}})
            t.query({'id':'nomethod','params':{'status':False}})
            t.query({'method':'toggleLed','params':{'status':False},'id':i})
            t.query({'method':'crap','params':{'status':False},'id':i})
            t.query({'method':'getMeasuredTemp','id':i})
        print "Test PASSED!!!"
    finally:
        t.close()
        
def testBadCmd():
    t = Thermostat('/dev/ttyACM0',115200)
    try:
        for i in range(1):
            t.query({'method':'getMeasuredTemp','id':i})
            t.query('this is not json',raw=True)
            t.query({'method':'getMeasuredTemp','id':i})
        print "Test PASSED!!!"
    finally:
        t.close()
    
if __name__=='__main__':
    test()