from agentic_chatbot import chatbot
from langchain_core.messages import HumanMessage, BaseMessage
import streamlit as st

st.title("Agentic Chatbot With LangGraph") 

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.text(message["content"])

user_input = st.chat_input("Type your message here...")
thread_id = "1"
config ={'configurable': {'thread_id': thread_id}}

if user_input:
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):
        assistant_content=st.write_stream(
            message_chunk.content[0]["text"] for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]}, config=config, stream_mode="messages"
            )
        )
        
    st.session_state['message_history'].append({"role": "assistant", "content": assistant_content})
    with st.chat_message('assistant'):
        st.text(assistant_content)
