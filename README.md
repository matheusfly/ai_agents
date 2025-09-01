# Multi-Agent Prompt Engine with LangGraph DAG Subgraphs

A sophisticated multi-agent prompt engineering system built using LangGraph with Directed Acyclic Graph (DAG) subgraphs. The system leverages local LLMs (Qwen3 and Gemma3) via Ollama to create a workflow for prompt analysis, task delegation, XML validation, and quality assurance.

## Features

- Multi-agent architecture with specialized roles
- DAG-based workflow with conditional routing
- Real-time verbose logging and agent reasoning visualization
- Human-in-the-loop (HITL) intervention points
- Stunning web UI with live updates and progress tracking
- Local LLM integration via Ollama
- LangSmith tracing for observability

## Architecture

The system consists of several specialized agents:

1. **Senior Reasoning Agent** (Qwen3) - Breaks down complex problems into step-by-step reasoning processes with detailed XML tagging
2. **Task Delegation Specialist** (Gemma3) - Creates detailed XML-formatted task delegation plans with clear agent assignments and dependencies
3. **XML Formatter & Validator** (Gemma3) - Ensures all inputs and outputs follow strict XML formatting standards with comprehensive validation
4. **Quality Assurance Specialist** (Qwen3) - Verifies the accuracy, completeness, and quality of all outputs before final delivery

## 🚨 Quick Fix for Ollama Connection Issues

If you're seeing "Error listing models: Failed to connect to Ollama" messages:

### Option 1: Quick Fix (Fastest)
```bash
python quick_fix.py
```

### Option 2: Full Setup (Recommended)
```bash
python setup_ollama.py
```

### Option 3: Manual Setup
1. **Install Ollama:**
   - Windows: Download from [https://ollama.com/download](https://ollama.com/download)
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Pull a model:**
   ```bash
   ollama pull llama3.2:1b
   ```

## Prerequisites

- Python 3.10+
- Ollama with Qwen3 and Gemma3 models
- Node.js (for UI components)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai_agents
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Ollama (Choose one method):**
   
   **🚀 Automated Setup (Recommended):**
   ```bash
   python setup_ollama.py
   ```
   
   **⚡ Quick Fix (If already partially set up):**
   ```bash
   python quick_fix.py
   ```
   
   **🔧 Manual Setup:**
   - Install Ollama from [https://ollama.com/](https://ollama.com/)
   - Start Ollama: `ollama serve`
   - Pull models: `ollama pull qwen2.5:7b` and `ollama pull gemma2:9b`

## Usage

**🎯 Easy Start:**
```bash
python start_system.py
```
This will start both the API server and web UI automatically.

**📊 Access the interfaces:**
- **Web UI:** http://localhost:8501
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

**🔧 Manual Start (Advanced):**
```bash
# Terminal 1: Start API server
uvicorn src.api.main:app --reload

# Terminal 2: Start Web UI
streamlit run src/ui/dashboard.py
```

## Project Structure

```
src/
├── agents/          # Agent implementations
├── workflow/        # LangGraph workflow definitions
├── api/             # FastAPI endpoints
├── ui/              # Web UI components
├── utils/           # Utility functions
└── config/          # Configuration files
```

## License

MIT