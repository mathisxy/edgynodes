import inspect
from typing import get_origin

from ....core.states import StateProtocol, SharedProtocol

class ToolContext[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol]:

    def __init__(self, state: T, shared: S) -> None:
        self.state = state
        self.shared = shared


    @classmethod
    def is_context_param(cls, parameter: inspect.Parameter) -> bool:
        annotation = parameter.annotation
        return annotation is cls or get_origin(annotation) is cls