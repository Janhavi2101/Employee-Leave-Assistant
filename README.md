# 🧠 Employee Leave Assistant

An AI-powered assistant that intelligently answers employee leave-related queries by parsing HR documents like employee records (CSV/JSON) and leave policy documents (PDF). Built with **FastAPI**, **React**, and integrated with **local or cloud LLMs** (e.g., via Ollama or Hugging Face), it serves as a smart backend system for HR automation.

---

## 🚀 Features

- 🔍 **Natural Language Q&A** over structured (employee CSV) and unstructured (PDF) documents
- 📂 **Multi-file parsing** (CSV/JSON + PDF)
- 🧠 **LLM Integration** (via Ollama or cloud API)
- 🧑‍💼 **Employee-specific answers** using filters like name or ID
- 💡 **Frontend** in React with live interaction
- ⚙️ **FastAPI backend** for robust REST API support
- 🔒 100% local model execution supported with **Ollama**

---


---

## 🔧 Tech Stack

| Layer | Tech |
|-------|------|
| 🧠 LLM | [Ollama](https://ollama.com/), [Mistral](https://mistral.ai/), [Phi-3](https://huggingface.co/microsoft/phi-3-mini-128k) |
| ⚙️ Backend | FastAPI, PyMuPDF (PDF parsing), Pandas |
| 💻 Frontend | React, Axios |
| 📚 Optional Tools | LangChain, LlamaIndex (for advanced context retrieval) |

---

## 📌 How It Works

1. User uploads employee records (CSV/JSON) and company policy (PDF)
2. The backend parses these documents and extracts relevant information
3. The user selects an employee and asks a natural language question
4. The backend:
   - Retrieves relevant context from the data
   - Sends it as a prompt to the local/cloud LLM
   - Returns a generated answer to the frontend

---

## ⚙️ Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

