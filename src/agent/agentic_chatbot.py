
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import sqlite3, uuid
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.tools.combined_tools import llm_with_tools, tools
from langgraph.graph.message import add_messages

load_dotenv()  # Load environment variables from .env file

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

#=========================Embedding for RAG=======================
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    # take user query from state
    """LLM node that can answer directly or call an appropriate tool."""

    system_message = SystemMessage(
        content=(
            "You are a helpful Agentic Chatbot with access to several tools.\n\n"

            "Tool usage instructions:\n"
            "- Use `rag_tool` for questions about the uploaded PDF or document. "
            "Always retrieve relevant document content before answering PDF-related questions.\n"
            "- Use `search_tool` for current events, recent information, or information "
            "that requires an internet search.\n"
            "- Use `calculator` for mathematical calculations. Do not calculate complex "
            "expressions manually when the calculator is available.\n"
            "- Use `get_stock_price` when the user asks for the current price of a stock.\n"
            "- Use `get_current_weather` when the user asks about current weather for a location.\n\n"

            "Answer general questions directly when no tool is required. "
            "Do not invent information from the uploaded document. "
            "If the user asks about a PDF but no document is available, ask them to upload a PDF. "
            "After receiving a tool result, provide a clear and helpful final answer."
        )
    )

    messages = [
        system_message,
        *state["messages"]
    ]
    response= llm_with_tools.invoke(messages)
    return {
        "messages":[response]
    }

# Nodes 2 - tool node
tool_node = ToolNode(tools)
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpoint = SqliteSaver(conn)

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpoint)

# initial_state = {
#     "messages": [HumanMessage(content="Hello! How are you?")]
#     }

# response = chatbot.invoke(initial_state)
# response["messages"][-1].content[0]["text"]

def get_all_thread():
    all_threads = set()
    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config['configurable']['thread_id'])
    return list(all_threads)

if __name__ == "__main__":
    thread_id = str(uuid.uuid4()) 
    while True:
        user_message = input("User: ")
        if user_message.strip().lower() in ['exit', 'quit', 'bye']:
            print("Exiting the chatbot. Goodbye!")
            break
        config = {'configurable': {'thread_id': thread_id}}
        response = chatbot.invoke({"messages": [HumanMessage(content=user_message)]}, config=config)
        
        