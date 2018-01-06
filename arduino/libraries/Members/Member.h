#ifndef MEMBER_H
#define MEMBER_H

#include "ArduinoJson.h"
#include "Arduino.h"

#define Member(type, name, value) \
	MemberProperty<type> name = MemberProperty<type>(#name, value)


// The Observer base class, its template parameter indicates the datatype of the parameters it expects to receive. Observers can only
// be connected to Signals with identical MemberTypes.
class Observer {
public:
    Observer() { }
    virtual ~Observer() { }
    // Allows the slot to be called by the signal during emmission
    virtual void operator() (JsonObject &change) = 0;

    // Allows the signal to take a copy of the slot so that it can maintain an internal reference to it upon connection.
    // Essentially a virtual copy consructor.
    virtual Observer* clone() = 0;
};

// The Signal class, we can implant these into ends and allow means to connect their members to them should they want to
// receive callbacks from their children means. Ofcourse it's possible that these callbacks are made within the context of
// an interrupt so the receipient will want to be fairly quick about how they process it.
template <class MemberType, int _maxObservers = 8> class MemberProperty {
    Observer* _observers[_maxObservers];
	int _nextObserver;
	MemberType _value;
	const char* _name;

public:
	MemberProperty(const char* name) {
    	_name = name;
    	_nextObserver = 0;
    }

	MemberProperty(const char* name, MemberType value) {
    	_name = name;
		_nextObserver = 0;
		_value = value;
	}

    // Since the signal takes copies of all the input _maxObservers via clone() it needs to clean up after itself when being destroyed.
    virtual ~MemberProperty() {
        for(int i = 0; i < _nextObserver; i++) {
            delete _observers[i];
        }
    }

    /**
     * Set the value of this member and
     * fire a change if needed.
     */
    void set(MemberType value) {
    	MemberType oldValue = _value;
    	_value = value;

    	if (value != oldValue) {
    		DynamicJsonBuffer buffer;
    		JsonObject &change = buffer.createObject();
    		change["name"] = _name;
    		change["type"] = "update";
    		change["old"] = oldValue;
    		change["value"] = _value;
    		notify(change);
    	}
    }

    MemberType get() {
    	return _value;
    }

    /**
     * Support assignment using equals operator
     */
    MemberType operator =(const MemberType& value) {
      this->set(value);
      return this->get();
    }

    /**
     * Support casting
     */
    operator MemberType() {
    	return this->get();
    }

    // Accepts a slot of the appropriate type and adds it to its list of _observers
    bool observe(Observer& observer) {
		// If we've run out of _maxObservers
		if(_nextObserver == (_maxObservers - 1)) {
			return false;
		}

		// Otherwise connect it up and away we go
		_observers[_nextObserver++] = observer.clone();
		return true;
	}

    bool unobserve(Observer& observer) {
    	return false; // TODO: Implement
    }

    // Notifies all the observers of the change
    void notify(JsonObject &change) {
        for(int i = 0; i < _nextObserver; i++) {
            (*_observers[i])(change);
        }
    }
//private:
//    int copy(int v) { return v;}
//    float copy(float v) { return v;}
//    bool copy(bool v) { return v;}
//    const char* copy(const char* v) {
//    	return String(v).c_str();
//    }


};


// PointerFunctionObserver is a subclass of Observer for use with function pointers. In truth there's not really any need to wrap up
// free standing function pointers into _maxObservers since any function in C/C++ is happy to accept a raw function pointer and execute
// it. However this system allows free standing functions to be used alongside member functions or even arbitrary functor objects.
class FunctionObserver : public Observer {
    typedef void (*FunctPtr)(JsonObject&);

    // A free standing function pointer
    FunctPtr funct;

public:
    FunctionObserver(FunctPtr _funct) : funct(_funct) { }

    // Copy the slot
    Observer *clone() {
    	return new FunctionObserver(this->funct);
    }

    // Execute the slot
    void operator() (JsonObject &change) {
    	return (funct)(change);
    }
};

// MemberFunctionObserver is a subclass of Observer that allows member function pointers to be used as _maxObservers. While free standing
// pointers to functions are relatively intuitive here, Members functions need an additional template parameter, the
// owner object type and they are executed via the ->* operator.
template <class ObjectType> class MethodObserver : public Observer {
    typedef void (ObjectType::*FunctPtr)(JsonObject&);;

    // The function pointer's owner object
    ObjectType *obj;

    // A function-pointer-to-method of class ObjectType
    FunctPtr funct;

public:
    MethodObserver(ObjectType *_obj, FunctPtr _funct) : obj(_obj), funct(_funct) { }

    // Copy the slot
    Observer *clone() {
    	return new MethodObserver<ObjectType>(this->obj, this->funct);
    }

    // Execute the slot
    void operator() (JsonObject &change) {
    	return (obj->*funct)(change);
    }
};


#endif // MEMBER_H
