from typing import Annotated, List, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class MessagesState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    messages_summary: NotRequired[str]
