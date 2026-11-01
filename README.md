RCA Troubleshooting Assistant 

An intelligent, AI-powered Root Cause Analysis (RCA) and Site Reliability Engineering (SRE) log troubleshooting platform. LogSentry AI combines local semantic vector retrieval (RAG), curated knowledge base solutions, and local Large Language Models (LLMs via Ollama) to analyze system logs, diagnose incidents, and recommend remediation steps.

---







. Ollama LLM Integration & Interactive AI Chat
- **New Ollama Service (`src/services/ollama_service.py`)**:
  - Local API communication with Ollama on `http://127.0.0.1:11434`.
  - Automatic model discovery (detects locally installed models like `llama3.2:latest`, `qwen2.5-coder:7b`).
  - Real-time token streaming (`stream_chat`) directly into Streamlit UI.
  - Structured incident context builder (`format_analysis_context`) that packages target environment, error stats, matched log lines, and Knowledge Base recommendations into the system prompt.
- **Configuration Updates (`config.yaml`)**:
  - Added `ollama` block with `base_url`, `default_model`, `temperature`, and specialized SRE `system_prompt`.
- **UI Enhancements (`app.py`)**:
  - **Sidebar Model Controls**: Live connection status badge (`🟢 Ollama Online`), model selection dropdown, and temperature slider.
  - **Results Tab — `💬 Ollama AI Chat`**: Dedicated chat tab inside analysis results with automatic RCA context attachment, context preview expander, custom context text area, 4 one-click quick prompt starters, and conversational chat history.
  - **Landing Page Tab — `💬 Chat with Ollama`**: Allows users to chat with the model and paste custom logs even before running an analysis.

---

## 📁 Project Directory Structure

```text
RCA/
├── app.py                             # Main Streamlit web application
├── config.yaml                        # Application configuration (paths, RAG, Ollama)
├── requirements.txt                   # Python package dependencies
├── README.md                          # Project documentation
├── data/
│   ├── kb/
│   │   └── fixes.json                 # Knowledge base of known issues & remediation steps
│   ├── logs/                          # Log repository (replaces external drive)
│   │   └── EMEA/
│   │       └── Barclays/
│   │           └── Unigy/
│   │               ├── 4.0/
│   │               │   ├── 4.0.0/
│   │               │   │   └── unigy_sample.log
│   │               │   └── 4.0.1/
│   │               │       ├── unigy_errors.error
│   │               │       └── unigy_service.log
│   └── vectors/                       # Precomputed FAISS vector indices & metadata
│       ├── kb_index.faiss
│       ├── kb_index_meta.pkl
│       └── log_index.pkl
├── src/
│   ├── models/
│   │   ├── knowledge_entry.py         # Knowledge base dataclass
│   │   └── log_entry.py               # Structured log entry dataclass
│   ├── services/
│   │   ├── embedding_service.py       # Sentence-transformers embedding wrapper
│   │   ├── knowledge_base.py          # KB retrieval & search service
│   │   ├── log_reader.py              # Log file discovery & parsing service
│   │   ├── ollama_service.py          # Ollama local LLM chat & streaming service
│   │   ├── rag_engine.py              # RAG query processing & matching engine
│   │   ├── vector_store.py            # FAISS vector store
│   │   └── vector_store_flexible.py   # Flexible FAISS vector store
│   └── utils/
│       ├── chunker.py                 # Text chunking utilities
│       └── parser.py                  # Regex log parser for standard log lines
└── venv/                              # Python virtual environment
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- [Ollama](https://ollama.com/) installed locally

### 1. Set Up the Virtual Environment
```powershell
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Ollama and Pull a Model
Ensure the Ollama daemon is running:
```powershell
# Start Ollama server
ollama serve

# Pull your preferred local model (e.g. Llama 3.2 or Qwen 2.5 Coder)
ollama run llama3.2
```

### 3. Run the Streamlit Application
```powershell
# Start Streamlit
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser.

---

## 📋 Log Format Specification

The built-in parser expects log lines formatted according to the following pattern:
```text
<ISO8601_TIMESTAMP>Z - <LEVEL> - Component=<NAME> - Code=<ERROR_CODE> - Severity=<LEVEL> - Message=<MESSAGE> - App=<APP_NAME>
```

**Example:**
```text
2025-12-18T01:58:10.105210Z - ERROR - Component=DBHandler - Code=E_TIMEOUT - Severity=HIGH - Message=Database query execution timeout after 30000ms - App=Unigy
2025-12-18T01:58:14.234567Z - ERROR - Component=DBHandler - Code=E_DB_FAIL - Severity=HIGH - Message=Database connection pool exhausted - App=Unigy
```

---

## 💡 Key Features

- **🔍 Automated Root Cause Analysis**: Identifies exact and semantic log matches against user troubleshooting queries.
- **📚 Curated Knowledge Base**: Maps extracted error codes (e.g. `E_DB_FAIL`, `E_TIMEOUT`) to verified engineering solutions.
- **📊 Analytics Dashboard**: Visualizes error distributions, timeline trends, and severity breakdowns using Plotly.
- **🤖 Context-Aware Ollama Chat**: Conversational AI assistant with full visibility into current incident telemetry, error codes, and KB fixes. Supports one-click prompt starters and custom context inputs.