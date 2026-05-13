import edgygraph
import discord
from llmir.messages import AIMessage
from llmir.roles import AIRoles

from ...core.states import StateProtocol, SharedProtocol


class AddEmptyAIMessageNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):
    """
    Adds an empty AI message to the end of the new AI messages list.
    """

    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            discord_message: discord.Message | None = shared.discord.messages[0] if shared.discord.messages else None
            bot_user = shared.discord.bot.user

        if not discord_message:
            raise ValueError("No messages in state to prepare AI message from.")

        role = AIRoles.MODEL if discord_message.author == bot_user else AIRoles.USER

        state.llm.new_messages.append(
            AIMessage(
                role=role,
                chunks=[]
            )
        )
        
