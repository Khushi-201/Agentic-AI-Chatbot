# Agentic AI Chatbot

An intelligent conversational agent built with **LangGraph** and **Google Gemini**, featuring multi-tool integration, RAG capabilities, and persistent conversation state management.

## 📋 Overview

This project implements an agentic chatbot that can:
- **Answer user queries** using Google Gemini as the language model
- **Retrieve information from PDFs** using Retrieval-Augmented Generation (RAG)
- **Search the web** for current events and recent information using Tavily
- **Perform calculations** with a built-in calculator
- **Fetch stock prices** in real-time
- **Provide weather information** for any location
- **Maintain conversation history** with SQLite-based state persistence
- **Manage multiple conversation threads** for concurrent dialogs

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│           Streamlit UI (app.py)                     │
│     - Chat interface                                │
│     - File upload for PDFs                          │
│     - Thread management                             │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────────┐  ┌───────────────────────┐
│  LangGraph Agent │  │  State Management     │
│  (agentic_       │  │  - SQLite Checkpointer│
│   chatbot.py)    │  │  - Thread Persistence │
│                  │  │  - Message History    │
└────────┬─────────┘  └───────────────────────┘
         │
    ┌────┴──────────────────────────────────┐
    │                                       │
    ▼                                       ▼
┌─────────────────┐            ┌───────────────────────┐
│ Chat Node       │            │ Tool Node            │
│ - LLM Call      │            │ - Execute Tools      │
│ (Gemini 3.5)    │            │ - Return Results     │
└─────────────────┘            └─────┬───────────────┘
                                      │
                    ┌─────────────────┼──────────────────┬──────────────┐
                    │                 │                  │              │
                    ▼                 ▼                  ▼              ▼
              ┌─────────────┐  ┌────────────┐    ┌──────────────┐  ┌─────────┐
              │  RAG Tool   │  │ Search Tool│    │ Calculator   │  │  Stock/ │
              │  (FAISS DB) │  │ (Tavily)   │    │  Weather Tools│ │ Weather │
              └─────────────┘  └────────────┘    └──────────────┘  └─────────┘
```

### Key Components

1. **Streamlit UI** (`app.py`)
   - Interactive chat interface
   - PDF upload functionality
   - Conversation thread management
   - Message history display

2. **Agentic Chatbot** (`src/agent/agentic_chatbot.py`)
   - LangGraph state machine with two main nodes:
     - **Chat Node**: Invokes LLM with tools
     - **Tool Node**: Executes selected tools
   - Conditional routing based on tool selection
   - SQLite-based state persistence

3. **Tools** (`src/tools/combined_tools.py`)
   - **RAG Tool**: PDF retrieval using FAISS vector store
   - **Search Tool**: Web search via Tavily API
   - **Calculator**: Mathematical computations
   - **Stock Price**: Real-time stock data
   - **Weather**: Current weather information

4. **Vector Store** (`faiss_db/`)
   - FAISS index for PDF embeddings
   - Google Generative AI embeddings

## ⚙️ Agent Decision Flow

The chatbot uses a sophisticated agentic workflow to decide which tools to use:

```
User Input (Chat Message)
       │
       ▼
┌─────────────────────────────────────────┐
│  1. Chat Node (LLM Decision Making)     │
│  ─────────────────────────────────────  │
│  • System prompt with tool instructions │
│  • Analyzes user query context          │
│  • Calls Gemini LLM with available tools│
│  • LLM decides if tools are needed      │
└────────┬────────────────────────────────┘
         │
         ├─ If no tool needed: Direct answer
         │                          │
         │                          ▼
         │                   Return response
         │
         └─ If tool needed: Tool selection
                                    │
                                    ▼
                    ┌───────────────────────────────────┐
                    │ 2. Conditional Router (Routing)   │
                    │ ─────────────────────────────────│
                    │ • Checks LLM response for tools   │
                    │ • Routes to Tool Node if needed   │
                    │ • Else routes back to Chat Node   │
                    └────────────┬──────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────────────┐
                    │ 3. Tool Node (Execution)          │
                    │ ─────────────────────────────────│
                    │ • Executes selected tool(s)       │
                    │ • Returns tool results to state   │
                    │ • Appends results to messages     │
                    └────────────┬──────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────────────┐
                    │ 4. Back to Chat Node (Response)   │
                    │ ─────────────────────────────────│
                    │ • LLM receives tool results       │
                    │ • Synthesizes final answer        │
                    │ • Formats response for user       │
                    └────────────┬──────────────────────┘
                                 │
                                 ▼
                        Return Final Response
```

**Tool Selection Logic:**
- **PDF/Document questions** → `rag_tool` (e.g., "What does the PDF say about X?")
- **Current events/Web info** → `search_tool` (e.g., "What's happening with X today?")
- **Math problems** → `calculator` (e.g., "Calculate 2+2 or solve this equation")
- **Stock inquiries** → `get_stock_price` (e.g., "What's the stock price of AAPL?")
- **Weather queries** → `get_current_weather` (e.g., "What's the weather in New York?")
- **General questions** → No tool (direct LLM response)

**State Persistence:**
- Each conversation is stored with a unique `thread_id`
- SQLite checkpointer persists state after each agent step
- Messages are accumulated in the `ChatState` using `add_messages`
- Users can load previous conversations by selecting the same thread

## 📄 Document Processing Workflow

When a user uploads a PDF, the following workflow is executed:

```
User Uploads PDF (app.py)
       │
       ▼
┌─────────────────────────────────────────────────┐
│ 1. File Reception & Validation                  │
│ ─────────────────────────────────────────────  │
│ • User selects PDF file in Streamlit interface  │
│ • File is validated and stored temporarily      │
│ • File path is passed to ingest_rag_document()  │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 2. Document Loading (combined_tools.py)         │
│ ─────────────────────────────────────────────  │
│ • PyPDFLoader extracts text from PDF            │
│ • Raw documents are loaded with metadata        │
│ • Metadata includes: source file, page numbers  │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 3. Text Chunking (Splitting)                    │
│ ─────────────────────────────────────────────  │
│ • RecursiveCharacterTextSplitter processes text │
│ • Chunk size: 1,000 characters                  │
│ • Overlap: 200 characters (context preservation)│
│ • Preserves sentence/paragraph boundaries       │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 4. Embedding Generation                         │
│ ─────────────────────────────────────────────  │
│ • Google Generative AI Embeddings converts      │
│   each chunk into a vector (embeddings)         │
│ • Model: gemini-embedding-001                   │
│ • Creates numerical representation of meaning   │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 5. Vector Store Indexing (FAISS)                │
│ ─────────────────────────────────────────────  │
│ • FAISS.from_documents() indexes embeddings     │
│ • Creates searchable vector index                │
│ • Saves index to faiss_db/ directory            │
│ • Enables fast similarity search                │
└────────────┬────────────────────────────────────┘
             │
             ▼
        Vector Store Ready
        
---

Retrieval Process (When User Queries PDF):

User Question About PDF
       │
       ▼
┌─────────────────────────────────────────────────┐
│ 1. Query Embedding                              │
│ ─────────────────────────────────────────────  │
│ • User query is embedded using same model       │
│ • Query vector created: gemini-embedding-001    │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 2. Similarity Search (FAISS)                    │
│ ─────────────────────────────────────────────  │
│ • Compares query embedding with chunk embeddings│
│ • Retrieves top-k most similar chunks (k=4)     │
│ • Based on cosine similarity score              │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 3. Document Formatting                          │
│ ─────────────────────────────────────────────  │
│ • Retrieved chunks formatted with metadata      │
│ • Includes: source file, page number, content   │
│ • Multiple documents clearly separated          │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 4. LLM Response Generation                      │
│ ─────────────────────────────────────────────  │
│ • Gemini LLM receives context + user query      │
│ • Synthesizes answer from retrieved content     │
│ • Cites source documents and page numbers       │
└────────────┬────────────────────────────────────┘
             │
             ▼
        Return Answer to User
```

**Key Parameters:**
- **Chunk Size**: 1,000 characters (balance between context and specificity)
- **Chunk Overlap**: 200 characters (ensures context isn't lost between chunks)
- **Retrieval k**: 4 documents (number of chunks retrieved per query)
- **Similarity Metric**: Cosine similarity (default for FAISS)
- **Embedding Model**: `gemini-embedding-001` (consistent with LLM)

**Advantages of This Approach:**
- 🔍 Semantic search finds relevant content regardless of exact keywords
- 📄 Multiple document support with source tracking
- ⚡ Fast retrieval using optimized FAISS index
- 🎯 Hybrid approach combines chunking strategy with embeddings
- 💾 Persistent storage allows reusing indexed documents

## 🚀 How to Run the Project

### Prerequisites

- Python 3.8+
- Google API Key (for Gemini and embeddings)
- Tavily API Key (for web search)
- Internet connection

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Agentic-AI-Chatbot
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

### Running the Application

1. **Start the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

2. **Access the chatbot:**
   - The application will open in your default browser at `http://localhost:8501`

3. **Using the chatbot:**
   - Type your questions in the chat input
   - Upload PDF files for document-based Q&A
   - Use the sidebar to manage different conversation threads
   - The agent will automatically select appropriate tools based on your query

### Running with Docker (Optional)

1. **Build the Docker image:**
   ```bash
   docker build -t agentic-chatbot .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 \
     -e GOOGLE_API_KEY=your_key \
     -e TAVILY_API_KEY=your_key \
     agentic-chatbot
   ```

## 📦 Dependencies

- **LangGraph**: Graph-based agentic framework
- **Streamlit**: Web UI framework
- **LangChain**: LLM integration and tools
- **Google Generative AI**: Gemini LLM and embeddings
- **Tavily**: Web search API
- **FAISS**: Vector similarity search
- **SQLite**: State persistence

See `requirements.txt` for the complete list.


## 🛠️ Development

To modify or extend the chatbot:

1. **Add new tools**: Add tool functions in `src/tools/combined_tools.py` with the `@tool` decorator
2. **Modify agent behavior**: Edit the chat node in `src/agent/agentic_chatbot.py`
3. **Customize UI**: Modify `app.py` for Streamlit interface changes

---

**Built with ❤️ using LangGraph and Google Gemini**
