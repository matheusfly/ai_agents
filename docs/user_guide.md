# Multi-Agent Prompt Engine User Guide

## Overview

The Multi-Agent Prompt Engine is a sophisticated system that uses multiple AI agents working together to analyze, process, and refine prompts through a structured workflow. The system leverages local LLMs via Ollama and provides a web-based dashboard for monitoring and interacting with the process.

## System Architecture

The system consists of four specialized AI agents:

1. **Senior Reasoning Agent** - Analyzes complex problems and breaks them down into structured reasoning steps
2. **Task Delegation Specialist** - Creates detailed task delegation plans with clear agent assignments
3. **XML Formatter & Validator** - Ensures all inputs and outputs follow strict XML formatting standards
4. **Quality Assurance Specialist** - Verifies the accuracy, completeness, and quality of all outputs

## Installation

### Prerequisites

- Python 3.10 or higher
- Ollama (for local LLM inference)
- Node.js (for UI components)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd multi-agent-prompt-engine
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama from [https://ollama.com/](https://ollama.com/)

4. Pull the required models:
   ```bash
   ollama pull qwen3:latest
   ollama pull gemma3:latest
   ```

## Running the System

### Starting the API Server

To start the FastAPI server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Starting the Web UI

To start the Streamlit dashboard:

```bash
streamlit run src/ui/dashboard.py
```

The UI will be available at `http://localhost:8501`

## Using the System

### Via Web UI (Recommended)

1. Open your browser and navigate to `http://localhost:8501`
2. Enter your prompt in the text area
3. Click "Process Prompt" to start the workflow
4. Monitor the agent logs in real-time
5. Review the results in the different tabs
6. Provide feedback if human review is requested

### Via API

The system provides several RESTful API endpoints:

- `POST /process-prompt` - Submit a prompt for processing
- `GET /session/{session_id}` - Get the status of a processing session
- `POST /submit-feedback` - Submit feedback for human review
- `GET /models` - List available models
- `GET /health` - Check system health

## Features

### Real-time Monitoring

The dashboard provides real-time updates of the agent workflow, including:
- Agent activity logs
- Performance timeline
- Log level distribution
- Workflow visualization

### Export Functionality

You can export session data and logs in multiple formats:
- JSON
- CSV
- XML

### Security

The system includes authentication and authorization mechanisms:
- Session-based authentication
- Role-based access control
- Audit logging

### Performance Monitoring

The system continuously monitors:
- CPU and memory usage
- Model performance
- Execution times
- Resource utilization

## Troubleshooting

### Common Issues

1. **Ollama server not running**
   - Ensure Ollama is installed and running
   - Check that the models are pulled (`ollama list`)

2. **API connection errors**
   - Verify the API server is running
   - Check the host and port configuration

3. **UI not loading**
   - Ensure all dependencies are installed
   - Check the browser console for errors

### Getting Help

For additional support, please check:
- The project documentation
- The issue tracker
- Community forums

## Contributing

We welcome contributions to the Multi-Agent Prompt Engine! Please see our contributing guidelines for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.