# run_project.ps1

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

# Run the program
Write-Host "Running the program..."
python main.py

# Deactivate virtual environment
deactivate

Write-Host "Program execution completed."