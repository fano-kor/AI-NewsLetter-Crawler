# run_project.ps1

# 명령줄 인수를 받아옵니다
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ScriptArgs
)

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Install packages from requirements.txt
Write-Host "Installing required packages..."
pip install -r requirements.txt

# Run the program with passed arguments
Write-Host "Running the program..."
python main.py $ScriptArgs

# Deactivate virtual environment
deactivate

Write-Host "Program execution completed."