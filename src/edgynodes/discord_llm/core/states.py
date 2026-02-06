import edgynodes as e # type: ignore


class _State(e.discord.State, e.llm.State):
    pass

class _Shared(e.discord.Shared, e.llm.Shared):
    pass