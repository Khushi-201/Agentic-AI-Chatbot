from agentic_chatbot import chatbot, get_all_thread
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
import streamlit as st
import uuid


st.title("Agentic Chatbot With LangGraph") 

# Generating new chat 
def generate_thread_id():
    return str(uuid.uuid4())

# Add current conversation to thread
def add_thread(thread_id):
    
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)
        
def reset_chat():
    
    #new chat, new thread, clearing current messages And add thread to conversation
    st.session_state["thread_id"]= generate_thread_id()
    st.session_state["message_history"] = []
    add_thread(st.session_state["thread_id"])
    
# Add this helper near the top of the file
def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""
    
# Load previous convo from the langgraph checkpointer for a specific convo

def load_conversations(thread_id):
    
    #get saved state for selected thread
    
    state= chatbot.get_state(
        config={
            "configurable":{
                "thread_id":thread_id
            }
        }
    )
    return state.values.get("messages", [])
    
#  ==================Sidebar thread feature==========================
  
#Adding Sidebar for conversation threads
st.sidebar.title("My Conversations")  

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()
        
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
    
if 'chat_threads' not in st.session_state:
    st.session_state["chat_threads"] = get_all_thread()
    
#After initializing the session state, add the current thread to the list of threads

add_thread(st.session_state["thread_id"])
    
        
# Display all coversations in thread in reverse order //new convo first
for thread_id in st.session_state["chat_threads"][::-1]:
    
    if st.sidebar.button(
    str(thread_id),
    key=thread_id
    ):
        #set selected thread as current thread
        st.session_state["thread_d"]=thread_id
        
        # load messages of that thread id
        messages= load_conversations(thread_id)
        
        #temp list for converting Langchain messages to
        #streamlit required message format
        
        temp_messages = []
        
        # loop through all saved messages
        for message in messages:
            
            if isinstance(message, HumanMessage):
                role = "user"
                
            elif isinstance(message, AIMessage):
                role = "assistant"
                
            else:
                continue
            
            # Convert langchain message into dictionary
            temp_messages.append({
                "role":role,
                "content": extract_text(message.content)
            })
            
        #replace current UI history with selected conversation
            
        st.session_state["message_history"]= temp_messages
        
        # rerun to desplay new loaded conversation
        st.rerun()
            
  # Need to show the previous conversations in the sidebar 
    
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.text(message["content"])          

user_input = st.chat_input("Type your message here...")
# thread_id = "1"
config = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_trace",
    }

if user_input:
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):
        assistant_content = st.write_stream(

            message_chunk.content[0]["text"]

            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]}, config=config, stream_mode="messages"
            )

            if isinstance(message_chunk, AIMessage)
            and message_chunk.content                              # not empty
            and isinstance(message_chunk.content[0], dict)          # is a dict block
            and message_chunk.content[0].get("type") == "text"      # is a text block
            and message_chunk.content[0].get("text")                # has non-empty text
        )

    st.session_state['message_history'].append({"role": "assistant", "content": assistant_content})