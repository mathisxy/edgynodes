import edgygraph as e

from .utils.temporary_message_controller import TemporaryMessageController


class StateAttribute(e.StateAttribute):
    pass

class SharedAttribute(e.SharedAttribute):
    controller: TemporaryMessageController


class State(e.State):
    discordtmp: StateAttribute

class Shared(e.Shared):
    discordtmp: SharedAttribute