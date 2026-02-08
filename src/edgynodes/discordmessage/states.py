import edgygraph
import discord


class StateAttribute(edgygraph.StateAttribute):
    pass

class SharedAttribute(edgygraph.SharedAttribute):
    message: discord.Message


class State(edgygraph.State):

    discordmessage: StateAttribute

class Shared(edgygraph.Shared):

    discordmessage: SharedAttribute