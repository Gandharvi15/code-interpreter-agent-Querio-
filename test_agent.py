import pandas as pd
from agent import run_agent
from safety import is_safe

# ── Test 1: Agent functionality ──────────────────────────────────
print("=== TEST 1: AGENT FUNCTIONALITY ===")
df = pd.read_csv("employees.csv")
answer = run_agent(df, "What is the average salary by department?")
print("\n===FINAL ANSWER===")
print(answer)

# ── Test 2: Safety blocking ──────────────────────────────────────
print("\n=== TEST 2: DANGEROUS CODE (should be blocked) ===")
dangerous = [
    "import os\nos.remove('file.txt')",
    "import subprocess\nsubprocess.call('shutdown')",
    "import shutil\nshutil.rmtree('/home')"
]

for code in dangerous:
    result, reason = is_safe(code)
    print(f"Safe: {result} | {reason or 'OK'}")

# ── Test 3: Safe code passthrough ────────────────────────────────
print("\n=== TEST 3: SAFE CODE (should pass) ===")
safe = [
    "import pandas as pd\ndf = pd.read_csv('temp_data.csv')\nprint(df.head())",
    "import pandas as pd\nprint(df.groupby('department')['salary'].mean())"
]

for code in safe:
    result, reason = is_safe(code)
    print(f"Safe: {result} | {reason or 'OK'}")