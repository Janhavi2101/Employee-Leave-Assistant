from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
import pandas as pd
import fitz  # PyMuPDF for PDF extraction
import io
from datetime import datetime
import torch
import os
import re

from transformers import pipeline
qa_pipeline = pipeline("text2text-generation", model="google/flan-t5-small")


app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
        if emp_file.filename.endswith(".csv"):
            content_bytes = emp_file.file.read()
            try:
                decoded = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded = content_bytes.decode("ISO-8859-1")
            df = pd.read_csv(io.StringIO(decoded))
        elif emp_file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(emp_file.file)
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported employee file format."})

        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        if "name" not in df.columns:
            return JSONResponse(status_code=400, content={"error": "Missing 'name' column in employee data."})
        df = df[df["name"].apply(lambda x: isinstance(x, str) and x.strip() != "")]
        employee_data.clear()
        employee_data.extend(df.to_dict(orient="records"))
        print("✅ Loaded Employees:", [e.get("name") for e in employee_data])

        if policy_file.filename.endswith(".pdf"):
            policy_data = policy_file.file.read()
            pdf_doc = fitz.open(stream=policy_data, filetype="pdf")
            policy_text = "".join(page.get_text() for page in pdf_doc)
            pdf_doc.close()
            print("✅ Extracted policy text.")
        else:
            return JSONResponse(status_code=400, content={"error": "Policy file must be a PDF."})

        return {"message": "Files uploaded and parsed successfully."}

    except Exception as e:
        print("❌ Upload error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/employees")
def get_employees():
    try:
        valid_names = [emp["name"] for emp in employee_data if isinstance(emp.get("name"), str) and emp["name"].strip()]
        print("👥 Available employees:", valid_names)
        return sorted(valid_names)
    except Exception as e:
        print("❌ Error in /employees:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask_question(query: Query):
    try:
        employee = find_employee(query.employee_name)
        if not employee:
            return JSONResponse(status_code=404, content={"answer": "Employee not found."})

        employee_info_str = "\n".join([f"{col.replace('_', ' ').title()}: {val}" for col, val in employee.items()])

        example_block = """
Examples:
Q: How many PL do I have left?
A: You have 20 Privilege Leave days remaining. You can apply as long as there are no LOP blocks and it's not a holiday/weekend.

Q: Can I take leave on 25-12-2025?
A: 25-12-2025 is a holiday, so Privilege Leave cannot be applied for that date.
"""

        instruction_block = """
Rules:
- PL (Privilege Leave) can only be applied if 'leave_balance_pl' > 0
- LTA requires 3 or more continuous PL days
- PL cannot be taken on weekends or holidays
- If LOP > 1 month, PL accrual is paused
- If unsure, say: "Please consult HR for more details."
"""

        extra_context = ""
        match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})", query.question)
        if match:
            try:
                date_str = match.group(1).replace("/", "-")
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                weekday = date_obj.strftime("%A")
                extra_context = f"\nNote: {date_str} is a {weekday}."
            except:
                pass

        prompt = f"""
You are a helpful HR assistant. Answer clearly and logically based on the records and policies.

Employee Record:
{employee_info_str}

Company Leave Policy:
{policy_text}

{instruction_block}
{example_block}
{extra_context}

Question:
{query.question}

Answer:
""".strip()

        print("🧠 Prompt sent to model:", prompt[:300], "...\n")
        output = qa_pipeline(prompt)[0]["generated_text"]
        return {"answer": output.strip()}

    except Exception as e:
        print("❌ Error in /ask:", e)
        return JSONResponse(status_code=500, content={"answer": "Internal Server Error"})
