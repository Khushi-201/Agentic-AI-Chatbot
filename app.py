from agent.agentic_chatbot import chatbot, get_all_thread
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
import streamlit as st
import uuid, os
import tempfile
from tools.combined_tools import ingest_rag_document 


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
    
# After initializing the session state, add the current thread to the list of threads

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

user_input = st.chat_input("Type your message here...",
                           accept_file = True,
                           file_type=["pdf"],)
# thread_id = "1"
config = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_trace",
    }

if user_input:
    prompt_text = user_input.text
    uploaded_files = user_input["files"]

    # If a PDF was attached, ingest it first
    if uploaded_files:
        for pdf_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_file.read())
                tmp_path = tmp_file.name

            with st.spinner(f"Processing {pdf_file.name}..."):
                ingest_rag_document(tmp_path)

            os.remove(tmp_path)
        st.toast(f"{len(uploaded_files)} PDF(s) ingested — you can now ask about them.")

    if prompt_text:                                              # only proceed to chat if there's text
        st.session_state['message_history'].append({"role": "user", "content": prompt_text})
        with st.chat_message('user'):
            st.text(prompt_text)

        with st.chat_message('assistant'):
            assistant_content = st.write_stream(

                message_chunk.content[0]["text"]

                for message_chunk, metadata in chatbot.stream(
                    {"messages": [HumanMessage(content=prompt_text)]}, config=config, stream_mode="messages"
                )

                if isinstance(message_chunk, AIMessage)
                and message_chunk.content
                and isinstance(message_chunk.content[0], dict)
                and message_chunk.content[0].get("type") == "text"
                and message_chunk.content[0].get("text")
            )

        st.session_state['message_history'].append({"role": "assistant", "content": assistant_content})