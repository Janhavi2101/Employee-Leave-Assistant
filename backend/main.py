from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import fitz  # PyMuPDF for PDF extraction
import io
import re
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# Load Gemma model (optimized for GPU deployment on Render)
model_id = "google/gemma-1.1-7b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16
)

qa_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=300)

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

employee_data = []
policy_text = ""

class Query(BaseModel):
    employee_name: str
    question: str

def find_employee(name):
    for emp in employee_data:
        emp_name = emp.get("name", "")
        if isinstance(emp_name, str) and emp_name.lower() == name.lower():
            return emp
    return None

@app.post("/upload")
async def upload_files(emp_file: UploadFile = File(...), policy_file: UploadFile = File(...)):
    global employee_data, policy_text
    try:
        # Load employee file
        if emp_file.filename.endswith(".csv"):
            content = emp_file.file.read()
            df = pd.read_csv(io.StringIO(content.decode("utf-8")))
        elif emp_file.filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(emp_file.file)
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported employee file format."})

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        if "name" not in df.columns:
            return JSONResponse(status_code=400, content={"error": "Missing 'name' column."})
        employee_data.clear()
        employee_data.extend(df.to_dict(orient="records"))

        # Extract text from PDF
        policy_bytes = policy_file.file.read()
        pdf = fitz.open(stream=policy_bytes, filetype="pdf")
        policy_text = "".join(page.get_text() for page in pdf)
        pdf.close()

        return {"message": "Files uploaded and processed."}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/employees")
def get_employees():
    try:
        return sorted([emp["name"] for emp in employee_data if emp.get("name")])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask_question(query: Query):
    try:
        employee = find_employee(query.employee_name)
        if not employee:
            return JSONResponse(status_code=404, content={"answer": "Employee not found."})

        emp_info = "\n".join([f"{k.title().replace('_', ' ')}: {v}" for k, v in employee.items()])
        date_hint = ""

        match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})", query.question)
        if match:
            try:
                date_str = match.group(1).replace("/", "-")
                dt = datetime.strptime(date_str, "%d-%m-%Y")
                weekday = dt.strftime("%A")
                date_hint = f"\nNote: {date_str} is a {weekday}."
            except:
                pass

        full_prompt = f"""
You are an HR assistant.

Employee Record:
{emp_info}

Company Policy:
{policy_text}

Rules:
- PL (Privilege Leave) requires positive balance.
- LTA needs 3+ continuous PL days.
- PL not valid on holidays/weekends.
- Long LOP blocks pause PL accrual.
- If unsure, say: "Please consult HR for more details."
{date_hint}

Question:
{query.question}

Answer:
""".strip()

        result = qa_pipeline(full_prompt)
        return {"answer": result[0]["generated_text"].replace(full_prompt, "").strip()}

    except Exception as e:
        return JSONResponse(status_code=500, content={"answer": f"Error: {str(e)}"})
