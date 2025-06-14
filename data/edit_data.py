import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

df = pd.read_csv(r"C:\Users\Janhavi\Desktop\project\data\emp_data_updated.csv", encoding="utf-8")
# -----------------------------
# Add new leave-related columns
# -----------------------------
today = datetime.today()

# Helper: generate random past date
def random_past_date(start_days_ago=30, end_days_ago=365):
    return (today - timedelta(days=random.randint(start_days_ago, end_days_ago))).strftime("%Y-%m-%d")

# Add columns with dummy but logical values
df["join_date"] = [random_past_date(500, 2000) for _ in range(len(df))]
df["last_leave_date"] = [random_past_date(10, 200) for _ in range(len(df))]
df["leave_balance_pl"] = np.random.randint(5, 91, size=len(df))          # 5 to 90 PL
df["leave_balance_sl_cl"] = np.random.randint(0, 13, size=len(df))       # 0 to 12 SL/CL
df["carry_forward_pl"] = np.random.randint(0, 31, size=len(df))          # 0 to 30 days carried
df["total_pl_taken_this_year"] = np.random.randint(0, 21, size=len(df))  # 0 to 20 PL taken
df["total_sl_cl_taken_this_year"] = np.random.randint(0, 13, size=len(df))  # 0 to 12 SL/CL taken
df["lop_taken"] = np.random.randint(0, 10, size=len(df))                 # LOP taken this year
df["is_on_lop_now"] = np.random.choice(["Yes", "No"], size=len(df))
df["leave_type_last_used"] = np.random.choice(["Privilege", "Sick", "Casual", "LOP"], size=len(df))

# -----------------------------
# Save updated file
# -----------------------------
df.to_csv(r"C:\Users\Janhavi\Desktop\project\data\emp_data_updated.csv", index=False)
print("✅ Leave columns added and file updated.")
