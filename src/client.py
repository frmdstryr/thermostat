import math
import json
import logging
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from atom.api import (
    Atom, FloatRange, Callable, Float, Enum, Int, Bool, Instance, Unicode
)

from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet.protocol import connectionDone
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.task import LoopingCall

log = logging.getLogger("enaml")


class RPCError(Exception):
    pass


class RPCProtocol(LineReceiver, object):
    def __init__(self):
        self._queue = OrderedDict()
        self.delimiter = '}'
        self.msgbuf = b''
        self._id = 0
        self._timeout = 3.0
    
    def __getattr__(self, attr):
        """ When no method or property is defined here,
              try to access the method remotely on the Thermostat
              by doing an RPC call.
        """
        if attr.startswith("_"):
            return super(RPCProtocol, self).__getattr__(attr)
        
        @inlineCallbacks
        def call(*args,**kwargs):
            if args and kwargs:
                raise RPCError("Can only do RPC calls with either args or "
                               "kwargs, not both.")
            params = args or kwargs
            self._id += 1
            request = {'method': attr, 'id': self._id, 'jsonrpc': '2.0'}
            if params:
                request['params'] = params
            log.info("request: {}".format(request))
            d = self.sendRequest(request)
            reactor.callLater(self._timeout, d.cancel)
            #log.info("waiting for response...")
            response = yield d
            log.info("response: {}".format(response))
            
            if 'result' in response:
                returnValue(response['result'])
            else:
                raise RPCError(response['error'])
        return call
    
    def connectionMade(self):
        super(RPCProtocol, self).connectionMade()
        log.info("Thermostat connection made")
        self.factory.onConnect()
    
    def lineReceived(self, line):
        #: Add the delimiter back on
        self.msgbuf += line+self.delimiter
        
        #: Called when we get a closing bracket    
        try:
            response = json.loads(self.msgbuf)
            self.msgbuf = b''
        except ValueError:
            #: Message not ready
            #log.info("message not yet ready {}".format(self.msgbuf))
            return
        log.debug("Received message: {}".format(response))
        req_id = response.get('id', None)
        if req_id:
            if req_id in self._queue:
                d = self._queue[req_id]
            else:
                # Set it as the most recent request ?
                req_id, d = self._queue.popitem(last=True)
                
            d.callback(response)
            del self._queue[req_id]
        else:
            self.msgReceived(response)
            
    def msgReceived(self, msg):
        log.info("Notification: {}".format(msg))
        self.factory.onNotify(msg)

    def sendRequest(self, request):
        """ Send an RPC request """
        msg = json.dumps(request)
        resp = Deferred()
        resp.time = datetime.now()
        self._clean()
        self._queue[request['id']] = resp
        self.transport.write(msg)
        return resp
    
    def _clean(self):
        #: Remove old items
        now = datetime.now()
        for k,d in self._queue.iteritems():
            if now-d.time > timedelta(seconds=30):
                del self._queue[k]
    
    def connectionLost(self, reason=connectionDone):
        super(RPCProtocol, self).connectionLost(reason)
        log.warning("Thermostat connection lost")
        

class Thermostat(ReconnectingClientFactory, Atom):
    #: Used to block sending updates 
    _syncing = Bool()
    _heartbeat = Instance(LoopingCall)
    _protocol = Instance(RPCProtocol)
    
    #: Validation precision for floats
    _precision = Int(12)

    #: Max delay between reconnect attempts (seconds)
    maxDelay = Int(5)
    
    #: Connected flag
    connected = Bool().tag(local=True)
    
    #: Status / error messges
    status = Unicode().tag(local=True)
    
    #: State variables 
    tempPin1 = Int(6)
    tempPin2 = Int(7)
    ledPin = Int(13)
    fanPin = Int(9)
    fireplacePin = Int(10)
    heatPin = Int(11)
    coolPin = Int(12)
    
    ledActive = Bool()
    fireplaceActive = Bool()
    fanActive = Bool()
    heatActive = Bool()
    coolActive = Bool()
    hysteresisTemp = FloatRange(low=0.2, high=10.0, value=0.6)
    desiredTemp = Float(24.0)
    insideTemp = Float(24.0).tag(readonly=True)
    insideHumidity = Float(50.0).tag(readonly=True)
    outsideTemp = Float(24.0).tag(readonly=True)
    outsideHumidity = Float(50.0).tag(readonly=True)

    wifiSsid = Unicode()
    wifiPass = Unicode()
    wifiIp = Unicode()

    fanPresent = Bool()
    fireplacePresent = Bool()
    heatPresent = Bool()
    coolPresent = Bool()
    
    heatMode = Enum("furnace", "fireplace")
    fanMode = Enum("off", "auto")
    systemMode = Enum("off", "heat", "cool")
    version = Unicode()

    #: Listen to messages
    listener = Callable()
    
    def __init__(self, *args, **kwargs):
        super(Thermostat, self).__init__(*args, **kwargs)
        self._heartbeat = LoopingCall(self.syncState)
        self.bindObservers()
        
    def startHeartbeat(self):
        self._heartbeat.start(30)
    
    def stopHeartbeat(self):
        if self._heartbeat.running:
            self._heartbeat.stop()
    
    def buildProtocol(self, addr):
        self.resetDelay()
        p = RPCProtocol()
        p.factory = self
        self._protocol = p
        return p
    
    def bindObservers(self):
        """ Bind _on_change to any members not tagged as readonly"""
        for name, m in self.members().items():
            if ((m.metadata and
                     (m.metadata.get('readonly', False) or
                      m.metadata.get('local', False)))
                    or name.startswith("_")):
                continue
            self.observe(name, self.onChange)
    
    def onConnect(self):
        self.status = "Connected"
        self.connected = True
        self.startHeartbeat()
    
    @inlineCallbacks      
    def syncState(self):
        try:
            state = yield self._protocol.getState()
        except Exception as e:
            log.warning("Failed to sync with thermostat: {}".format(
                traceback.format_exc()))
            self._protocol.transport.loseConnection()
            return        
            
        self._syncing = True
        try:
            for k, v in state.items():
                if hasattr(self, k):
                    try:
                        setattr(self, k, v)
                    except Exception as e:
                        log.warning("Failed to sync with thermostat: "
                                    "{} {}".format(k, v))
        finally:
            self._syncing = False        
    
    @inlineCallbacks
    def onChange(self, change): 
        """ Called when one of the members changes. 
            Sends RPC command to set the state on the Thermostat.
            @param change: member change dict from this object
        """
        if self.listener:
            self.listener(change)
        if self.connected and not self._syncing:
            prec = self._precision
            try:
                k, v = change['name'], change['value']
                
                #: Submit the change
                state = yield self._protocol.setState(**{k:v})
                
                #: Verify the change
                result = state.get(k, change['oldvalue'])
                
                #: Special case for float rounding errors
                ok = True
                if type(result) == float:
                    if round(result, prec) != round(v, prec):
                        ok = False
                elif result != v:
                    ok = False
                
                #: Undo change in UI
                if not ok:
                    log.error("Failed to update value {} to {}, "
                              "got {}".format(k, v, result))
                    self._syncing = True
                    try:
                        setattr(self, k, change['oldvalue'])
                    finally:
                        self._syncing = False
            except Exception as e:
                log.error("Error updating thermostat: "
                          "{} {}".format(type(e), e))
    
    def onNotify(self, change):
        """ Called when a notification is received from the thermostat. 
            Updates the state variable.
            @param change: member change dict from thermostat
        """
        if self.listener:
            self.listener(change)
        if change.get('type', None) == 'update':
            k, v = change['name'], change['value']
            self._syncing = True
            try:
                # Discard all nan values
                if isinstance(v, float) and math.isnan(v):
                    return
                if hasattr(self, k):
                    setattr(self, k, v)
            except Exception as e:
                log.error("Failed to sync with thermostat: {} {}".format(k, v))
            finally:
                self._syncing = False
            
    def clientConnectionLost(self, connector, reason):
        self.status = 'Connection lost. Reason: {}'.format(reason)
        self.connected = False
        self.stopHeartbeat()
        super(Thermostat, self).clientConnectionLost(connector, reason)

    def clientConnectionFailed(self, connector, reason):
        self.status = 'Connection failed. Reason: {}'.format(reason)
        self.connected = False
        self.stopHeartbeat()
        super(Thermostat, self).clientConnectionFailed(connector, reason)
