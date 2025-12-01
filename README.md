## 🛠️ Installation & Setup

### 1. Python Environment
It is highly recommended to use a virtual environment.

```bash
# 1. Create Virtual Environment
python -m venv venv

# 2. Activate Environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Run comparative analysis from root directory (.../aadcourseproject)
python -m heuristics.analyse

# 5. View the report in analysis_output/analysis_report.pdf