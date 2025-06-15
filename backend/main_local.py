from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import fitz  # PyMuPDF for PDF extraction
import io
from datetime import datetime, timedelta
import torch
import os
import re
import json
from typing import Dict, Any, List
import warnings

warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
employee_data = []
policy_text = ""

qa_pipeline = None

def initialize_model():
    global qa_pipeline
    
    qa_models_to_try = [
        "distilbert-base-uncased-distilled-squad",
        "distilbert-base-cased-distilled-squad", 
        "deepset/roberta-base-squad2",
        "deepset/minilm-uncased-squad2",
        "bert-large-uncased-whole-word-masking-finetuned-squad"
    ]
    
    for model_name in qa_models_to_try:
        try:
            print(f"🔄 Trying to load QA model: {model_name}...")
            
            try:
                # First try: Normal loading
                qa_pipeline = pipeline(
                    "question-answering", 
                    model=model_name,
                    device=-1,  
                    trust_remote_code=True
                )
                print(f"✅ Successfully loaded {model_name}")
                return True
                
            except Exception as network_error:
                if any(keyword in str(network_error).lower() for keyword in ['connection', 'network', 'timeout', 'resolve']):
                    print(f"🌐 Network issue with {model_name}: {str(network_error)[:100]}...")
                    
                    # Try with different timeout settings
                    try:
                        import requests
                        requests.adapters.DEFAULT_TIMEOUT = 60
                        
                        qa_pipeline = pipeline(
                            "question-answering", 
                            model=model_name,
                            device=-1,
                            trust_remote_code=True,
                            use_fast=False  
                        )
                        print(f"✅ Successfully loaded {model_name} with extended timeout")
                        return True
                    except:
                        print(f"❌ Still failed with extended timeout for {model_name}")
                        continue
                else:
                    print(f"❌ Non-network error with {model_name}: {network_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Failed to load {model_name}: {e}")
            continue
    
    print("❌ All QA models failed to load due to network issues.")
    print("🔧 Suggestions to fix:")
    print("   1. Check your internet connection")
    print("   2. Try using a VPN if HuggingFace is blocked")
    print("   3. Consider downloading models manually for offline use")
    print("💡 System will use advanced rule-based responses instead!")
    return False

# Initialize model
print("🤖 Initializing AI models...")
model_loaded = initialize_model()

class Query(BaseModel):
    employee_name: str
    question: str

def clean_dataframe_columns(df):
    """Clean and standardize dataframe columns"""
    # Strip whitespace and standardize column names
    df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
    
    # Handle common column name variations
    column_mapping = {
        'employee_name': 'name',
        'emp_name': 'name',
        'employee_id': 'emp_id',
        'pl_balance': 'leave_balance_pl',
        'privilege_leave': 'leave_balance_pl',
        'casual_leave': 'leave_balance_cl',
        'cl_balance': 'leave_balance_cl',
        'sick_leave': 'leave_balance_sl',
        'sl_balance': 'leave_balance_sl'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    
    return df

def find_employee(name: str) -> Dict[str, Any]:
    """Find employee by name with fuzzy matching"""
    if not name or not name.strip():
        return None
        
    name_lower = name.lower().strip()
    
    # Exact match first
    for emp in employee_data:
        emp_name = str(emp.get("name", "")).lower().strip()
        if emp_name == name_lower:
            return emp
    
    # Partial match
    for emp in employee_data:
        emp_name = str(emp.get("name", "")).lower().strip()
        if name_lower in emp_name or emp_name in name_lower:
            return emp
    
    return None

def extract_dates_from_text(text: str) -> List[str]:
    """Extract dates from text in various formats"""
    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY/MM/DD or YYYY-MM-DD
        r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b'  # DD Mon YYYY
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

def safe_float_convert(value):
    """Safely convert value to float"""
    if value is None or value == '' or pd.isna(value):
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def analyze_leave_request(employee: Dict[str, Any], question: str, policy: str) -> str:
    """Analyze leave request with enhanced rule-based logic"""
    question_lower = question.lower()
    
    # Extract employee leave balances safely
    pl_balance = safe_float_convert(employee.get('leave_balance_pl', 0))
    cl_balance = safe_float_convert(employee.get('leave_balance_cl', 0))
    sl_balance = safe_float_convert(employee.get('leave_balance_sl', 0))
    lop_days = safe_float_convert(employee.get('lop_days', 0))
    
    # Check for leave balance queries
    if any(word in question_lower for word in ['balance', 'left', 'remaining', 'available', 'how many']):
        if 'pl' in question_lower or 'privilege' in question_lower:
            return f"You have {pl_balance} Privilege Leave (PL) days remaining."
        elif 'cl' in question_lower or 'casual' in question_lower:
            return f"You have {cl_balance} Casual Leave (CL) days remaining."
        elif 'sl' in question_lower or 'sick' in question_lower:
            return f"You have {sl_balance} Sick Leave (SL) days remaining."
        else:
            return f"Your leave balance:\n• Privilege Leave (PL): {pl_balance} days\n• Casual Leave (CL): {cl_balance} days\n• Sick Leave (SL): {sl_balance} days"
    
    # Check for leave application queries
    if any(word in question_lower for word in ['apply', 'take', 'request', 'can i', 'want to']):
        dates = extract_dates_from_text(question)
        
        if dates:
            date_str = dates[0]
            try:
                if len(date_str) == 3:  # DD Mon YYYY format
                    day, month, year = date_str
                    month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                               'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                    month_num = month_map.get(month.lower()[:3])
                    if month_num:
                        date_obj = datetime(int(year), month_num, int(day))
                else:
                    # Assume DD/MM/YYYY format
                    day, month, year = date_str if len(date_str) == 3 else (date_str[2], date_str[1], date_str[0])
                    date_obj = datetime(int(year), int(month), int(day))
                
                weekday = date_obj.strftime("%A")
                
                if weekday in ['Saturday', 'Sunday']:
                    return f"❌ Leave cannot be applied for {date_obj.strftime('%d-%m-%Y')} as it falls on a {weekday} (weekend)."
                
                if date_obj.date() < datetime.now().date():
                    return f"❌ Leave cannot be applied for {date_obj.strftime('%d-%m-%Y')} as it's in the past."
                
                # Check leave type and balance
                if 'pl' in question_lower or 'privilege' in question_lower:
                    if pl_balance <= 0:
                        return f"❌ You cannot apply for Privilege Leave on {date_obj.strftime('%d-%m-%Y')} as you have no PL balance remaining ({pl_balance} days)."
                    elif lop_days > 30:
                        return f"⚠️  PL accrual is paused due to LOP exceeding 30 days. Current LOP: {lop_days} days."
                    else:
                        return f"✅ You can apply for Privilege Leave on {date_obj.strftime('%d-%m-%Y')} ({weekday}). Current PL balance: {pl_balance} days."
                
                elif 'cl' in question_lower or 'casual' in question_lower:
                    if cl_balance <= 0:
                        return f"❌ You cannot apply for Casual Leave on {date_obj.strftime('%d-%m-%Y')} as you have no CL balance remaining ({cl_balance} days)."
                    else:
                        return f"✅ You can apply for Casual Leave on {date_obj.strftime('%d-%m-%Y')} ({weekday}). Current CL balance: {cl_balance} days."
                
                elif 'sl' in question_lower or 'sick' in question_lower:
                    if sl_balance <= 0:
                        return f"❌ You cannot apply for Sick Leave on {date_obj.strftime('%d-%m-%Y')} as you have no SL balance remaining ({sl_balance} days)."
                    else:
                        return f"✅ You can apply for Sick Leave on {date_obj.strftime('%d-%m-%Y')} ({weekday}). Current SL balance: {sl_balance} days."
                
                else:  # General leave application
                    total_balance = pl_balance + cl_balance + sl_balance
                    if total_balance <= 0:
                        return f"❌ You cannot apply for leave on {date_obj.strftime('%d-%m-%Y')} as you have no leave balance remaining."
                    else:
                        return f"✅ You can apply for leave on {date_obj.strftime('%d-%m-%Y')} ({weekday}). Available balance: PL: {pl_balance}, CL: {cl_balance}, SL: {sl_balance} days."
                
            except (ValueError, TypeError, KeyError) as e:
                return f"⚠️  Could not parse the date. Please use format DD/MM/YYYY or DD-MM-YYYY."
        
        # General leave application guidance without specific date
        total_balance = pl_balance + cl_balance + sl_balance
        if total_balance <= 0:
            return "❌ You have no leave balance remaining. Please consult HR for guidance."
        
        return f"📋 Based on your current balance (PL: {pl_balance}, CL: {cl_balance}, SL: {sl_balance}), you can apply for leave. Please specify the date and leave type for detailed guidance."
    
    # Check for policy queries
    if any(word in question_lower for word in ['policy', 'rule', 'eligible', 'how much', 'minimum']):
        if policy:
            policy_snippet = policy[:300] + "..." if len(policy) > 300 else policy
            return f"📋 Based on the company policy: {policy_snippet}\n\nFor detailed policy information, please consult the full policy document or HR."
        else:
            return "📋 Please refer to your company's leave policy document or consult HR for policy-related questions."
    
    return None

def create_qa_context(employee: Dict[str, Any], question: str, policy: str) -> tuple:
    """Create context and question for question-answering model"""
    # Format employee data clearly
    employee_info = []
    for key, value in employee.items():
        if value != '' and value is not None and not pd.isna(value):
            formatted_key = key.replace('_', ' ').title()
            employee_info.append(f"{formatted_key}: {value}")
    
    employee_summary = ". ".join(employee_info)
    
    # Create focused context
    policy_excerpt = policy[:600] if len(policy) > 600 else policy
    
    context = f"Employee Information: {employee_summary}. Company Policy: {policy_excerpt}"
    
    return context, question

def create_text2text_prompt(employee: Dict[str, Any], question: str, policy: str) -> str:
    """Create prompt for text-to-text generation models"""
    # Format employee data
    employee_info = []
    for key, value in employee.items():
        if value != '' and value is not None and not pd.isna(value):
            formatted_key = key.replace('_', ' ').title()
            employee_info.append(f"{formatted_key}: {value}")
    
    employee_summary = ". ".join(employee_info)
    
    # Shorter, more focused prompt for smaller models
    prompt = f"Answer this question about the employee: {question}\nEmployee data: {employee_summary}\nAnswer:"
    
    return prompt

def validate_response(response: str, employee: Dict[str, Any], question: str) -> str:
    """Validate and improve the AI response"""
    if not response or len(response.strip()) < 3:
        return analyze_leave_request(employee, question, policy_text) or "I need more specific information to help you with your query."
    
    response_lower = response.lower()
    question_lower = question.lower()
    
    # Check if response is just echoing the question
    if question.lower().strip() in response.lower().strip():
        return analyze_leave_request(employee, question, policy_text) or "I need more specific information to help you with your query."
    
    # Check for generic/unhelpful responses
    unhelpful_phrases = ['i don\'t know', 'i cannot', 'i\'m not sure', 'please consult', 'i am not able']
    if any(phrase in response_lower for phrase in unhelpful_phrases):
        rule_based_answer = analyze_leave_request(employee, question, policy_text)
        if rule_based_answer:
            return rule_based_answer
    
    return response.strip()

@app.post("/upload")
async def upload_files(emp_file: UploadFile = File(...), policy_file: UploadFile = File(...)):
    global employee_data, policy_text

    try:
        print(f"📁 Processing employee file: {emp_file.filename}")
        
        # Process employee file
        if emp_file.filename.endswith(".csv"):
            content_bytes = await emp_file.read()
            try:
                decoded = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    decoded = content_bytes.decode("ISO-8859-1")
                except UnicodeDecodeError:
                    decoded = content_bytes.decode("utf-8", errors='ignore')
            df = pd.read_csv(io.StringIO(decoded))
        elif emp_file.filename.endswith((".xlsx", ".xls")):
            content_bytes = await emp_file.read()
            df = pd.read_excel(io.BytesIO(content_bytes))
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported employee file format. Use CSV or Excel."})

        print(f"📊 Original columns: {list(df.columns)}")
        
        # Clean and standardize the dataframe
        df = clean_dataframe_columns(df)
        
        print(f"📊 Cleaned columns: {list(df.columns)}")
        
        # Validate required columns
        if "name" not in df.columns:
            available_cols = [col for col in df.columns if 'name' in col.lower()]
            error_msg = f"Missing 'name' column in employee data. Available columns: {list(df.columns)}"
            if available_cols:
                error_msg += f". Did you mean: {available_cols}?"
            return JSONResponse(status_code=400, content={"error": error_msg})
        
        # Filter out empty names and clean data
        df = df[df["name"].notna()]
        df = df[df["name"].astype(str).str.strip() != ""]
        
        # Fill NaN values with empty strings for better handling
        df = df.fillna('')
        
        # Convert to records and store
        employee_data.clear()
        employee_data.extend(df.to_dict(orient="records"))
        
        print(f"✅ Loaded {len(employee_data)} employees")
        print(f"📝 Sample employees: {[e.get('name') for e in employee_data[:3]]}")
        print(f"📊 Available columns: {list(df.columns)}")

        # Process policy file
        print(f"📋 Processing policy file: {policy_file.filename}")
        
        if policy_file.filename.endswith(".pdf"):
            policy_bytes = await policy_file.read()
            try:
                pdf_doc = fitz.open(stream=policy_bytes, filetype="pdf")
                policy_text = ""
                for page_num, page in enumerate(pdf_doc):
                    page_text = page.get_text()
                    policy_text += page_text
                pdf_doc.close()
                print(f"✅ Extracted {len(policy_text)} characters from {page_num + 1} pages")
            except Exception as pdf_error:
                print(f"❌ PDF processing error: {pdf_error}")
                policy_text = "Policy document could not be processed."
        else:
            return JSONResponse(status_code=400, content={"error": "Policy file must be a PDF."})

        return {"message": f"✅ Files uploaded successfully! Loaded {len(employee_data)} employees and policy document ({len(policy_text)} characters)."}

    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Upload failed: {str(e)}"})

@app.get("/employees")
def get_employees():
    try:
        valid_names = []
        for emp in employee_data:
            name = emp.get("name")
            if name and isinstance(name, str) and name.strip():
                valid_names.append(name.strip())
        
        unique_names = sorted(list(set(valid_names)))
        print(f"👥 Available employees: {len(unique_names)}")
        return unique_names
    except Exception as e:
        print(f"❌ Error in /employees: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/status")
def get_status():
    """Get system status"""
    return {
        "employees_loaded": len(employee_data),
        "policy_loaded": len(policy_text) > 0,
        "policy_length": len(policy_text),
        "ai_model_loaded": model_loaded,
        "system_status": "✅ Ready" if employee_data and policy_text else "⚠️  Waiting for file upload"
    }

@app.post("/ask")
async def ask_question(query: Query):
    try:
        print(f"❓ Question from {query.employee_name}: {query.question}")
        
        # Validate inputs
        if not query.employee_name or not query.employee_name.strip():
            return JSONResponse(status_code=400, content={"answer": "❌ Employee name is required."})
        
        if not query.question or not query.question.strip():
            return JSONResponse(status_code=400, content={"answer": "❌ Question is required."})
        
        # Check if data is loaded
        if not employee_data:
            return JSONResponse(status_code=400, content={"answer": "❌ No employee data loaded. Please upload employee file first."})
        
        # Find employee
        employee = find_employee(query.employee_name)
        if not employee:
            available_employees = [emp.get("name", "") for emp in employee_data[:10]]
            return JSONResponse(
                status_code=404, 
                content={"answer": f"❌ Employee '{query.employee_name}' not found.\n\n📋 Available employees include:\n" + "\n".join([f"• {name}" for name in available_employees[:10]])}
            )

        print(f"👤 Found employee: {employee.get('name')}")

        # Use rule-based analysis first (more reliable)
        rule_based_answer = analyze_leave_request(employee, query.question, policy_text)
        if rule_based_answer:
            print("✅ Used rule-based response")
            return {"answer": rule_based_answer}

        # Use AI model as fallback only if available AND it's a QA model
        if qa_pipeline and model_loaded:
            try:
                print("🤖 Using QA model for response")
                
                # Since we only load QA models now, we can directly use question-answering approach
                context, question = create_qa_context(employee, query.question, policy_text)
                
                # Use the QA pipeline
                result = qa_pipeline(question=question, context=context)
                ai_response = result.get('answer', '')
                
                # Validate and improve response
                if ai_response and len(ai_response.strip()) > 5:
                    final_answer = validate_response(ai_response, employee, query.question)
                    print(f"✅ QA model response: {final_answer[:100]}...")
                    return {"answer": final_answer}
                
            except Exception as ai_error:
                print(f"❌ QA model error: {ai_error}")
                print("🔄 Falling back to rule-based system...")
        
        # Final fallback: return structured employee info with guidance
        emp_info_lines = []
        for key, value in employee.items():
            if value != '' and value is not None and not pd.isna(value):
                formatted_key = key.replace('_', ' ').title()
                emp_info_lines.append(f"• {formatted_key}: {value}")
        
        emp_info = "\n".join(emp_info_lines)
        
        question_lower = query.question.lower()
        guidance = ""
        
        if any(word in question_lower for word in ['balance', 'left', 'remaining']):
            guidance = "\n\n💡 For leave balance queries, check the 'Leave Balance', 'Carry Forward' fields above."
        elif any(word in question_lower for word in ['apply', 'take', 'request']):
            guidance = "\n\n💡 For leave applications, ensure you have sufficient balance and the date is not a weekend/holiday."
        elif any(word in question_lower for word in ['policy', 'rule', 'eligible']):
            guidance = "\n\n💡 For policy questions, please refer to your company's leave policy document or consult HR."
        
        return {"answer": f"👤 **Employee Information for {employee.get('name', 'Unknown')}:**\n\n{emp_info}{guidance}"}

    except Exception as e:
        print(f"❌ Error in /ask: {str(e)}")
        return JSONResponse(status_code=500, content={"answer": f"❌ Sorry, I encountered an error: {str(e)}. Please try again."})

@app.get("/")
def read_root():
    return {"message": "🚀 Employee Leave Management API is running!", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)