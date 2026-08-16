
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()  # Load environment variables from .env file

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    # take user query from state
    messages = state['messages']
    response= llm.invoke(messages)
    return {
        "messages":[response]
    }


checkpoint = MemorySaver()
graph =StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpoint)


# initial_state = {
#     "messages": [HumanMessage(content="Hello! How are you?")]
#     }

# response = chatbot.invoke(initial_state)
# response["messages"][-1].content[0]["text"]


if __name__ == "__main__":
    thread_id = "1"
    while True:
        user_message = input("User: ")
        if user_message.strip().lower() in ['exit', 'quit', 'bye']:
            print("Exiting the chatbot. Goodbye!")
            break
        config = {'configurable': {'thread_id': thread_id}}
        response = chatbot.invoke({"messages": [HumanMessage(content=user_message)]}, config=config)


