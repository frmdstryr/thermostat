import os
import sys
import cPickle as pickle
from atom.api import Atom, Constant, Int, List, Member
from enaml.application import timed_call


def clip(s, n=16):
    """ Clip the string to the given length if needed"""
    s = str(s)
    return s[:n]


class Model(Atom):
    """ An atom object that can exclude members from it's state
    by tagging the member with .tag(persist=False)

    """

    def __getstate__(self):
        """ Exclude any members from the state that are
        tagged with `persist=False`.

        """
        state = super(Model, self).__getstate__()
        for name, member in self.members().items():
            metadata = member.metadata
            if name in state and metadata and \
                    not metadata.get('persist', True):
                del state[name]
        return state

    def __setstate__(self, state):
        """  Set the state ignoring any fields that fail to set which
        may occur due to version changes.

        """
        for key, value in state.items():
            try:
                setattr(self, key, value)
            except Exception as e:
                print("Warning: Failed to restore state "
                      "'{}.{} = {}': {}".format(
                      self, key, clip(value, n=100), e
                ))


class State(Model):
    """ An Atom object that automatically saves and restores it's state
    when a member changes. Saves are queued and fired once to reduce save

    """
    _instance = None

    #: File where state is saved within the assets folder
    #: relative to assets/python. By default this is outside the python
    #: folder so it is not overwritten when a new version of the app
    #: is installed (ex. otherwise when you push an update to the Play store
    #: it will overwrite the users saved state!)
    _state_file = Constant(os.path.join(sys.path[0], '../state.db'))
    _state_save_pending = Int().tag(persist=False)
    _state_members = List(Member).tag(persist=False)

    @classmethod
    def instance(cls):
        """ Get an instance of this object """
        if State._instance is None:
            cls()
        return State._instance

    def __init__(self, *args, **kwargs):
        """ Create an instance of the state. This should only be called
        once or a RuntimeError will be raised.

        """
        if State._instance is not None:
            raise RuntimeError("Only one instance of AppState can exist!")
        super(State, self).__init__(*args, **kwargs)
        State._instance = self
        self._bind_observers()

    # -------------------------------------------------------------------------
    # State API
    # -------------------------------------------------------------------------
    def save(self):
        """ Manually trigger a save """
        self._queue_save_state({'type': 'manual'})

    def _bind_observers(self):
        """ Try to load the plugin state """
        #: Build state members list
        for name, member in self.members().items():
            if not member.metadata or member.metadata.get('persist', True):
                self._state_members.append(member)

        #: Get the valid state keys
        persistent_members = [m.name for m in self._state_members]
        print("State members: {}".format(persistent_members))

        #: Load the state from disk
        try:
            with open(self._state_file, 'rb') as f:
                state = pickle.load(f)

            #: Delete anything that may have changed
            for k, v in state.items():
                if k not in persistent_members:
                    del state[k]
            print("Restoring state: {}".format(state))
            self.__setstate__(state)
        except Exception as e:
            print("Failed to load state: {}".format(e))

        #: Hook up observers to automatically save when a change occurs
        for m in self._state_members:
            self.observe(m.name, self._queue_save_state)

    def _queue_save_state(self, change):
        """ Queue a save state. This calls _save_state after a given duration
        so that multiple state changes get batched and saved all at once
        instead of saving multiple times (which a become slow).

        """
        if change['type'] in ['update', 'manual', 'container']:
            self._state_save_pending += 1
            timed_call(350, self._save_state, change)

    def _save_state(self, change):
        """ Actually save the state once all the pending state changes
        settle out (when _state_save_pending==0).

        """
        #: Wait until the last change occurs
        self._state_save_pending -= 1
        if self._state_save_pending != 0:
            return

        #: Actually change
        try:
            print("Saving state due to change: {}".format(change))

            #: Dump first so any failure to encode doesn't wipe out the
            #: previous state

            state = self.__getstate__()
            for k in state:
                if k in self._state_members:
                    del state[k]
            state = pickle.dumps(state)

            with open(self._state_file, 'wb') as f:
                f.write(state)
        except Exception as e:
            print("Failed to save state: {}".format(e))

    def _unbind_observers(self):
        """ Stop observing the state. """
        for member in self._state_members:
            self.unobserve(member.name, self._queue_save_state)