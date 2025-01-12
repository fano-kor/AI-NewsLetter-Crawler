# run_project.ps1

param(
    [Parameter(Mandatory=$false)]
    [Alias("i")]
    [switch]$Immediate,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
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

# Prepare arguments for main.py
$MainArgs = @()
if ($Immediate) {
    $MainArgs += "--immediate"
}
if ($RemainingArgs) {
    $MainArgs += $RemainingArgs
}

# Run the program with passed arguments
Write-Host "Running the program..."
python main.py $MainArgs

# Deactivate virtual environment
deactivate

Write-Host "Program execution completed."
