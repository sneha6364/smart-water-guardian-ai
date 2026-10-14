$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $node) { Write-Host "Node.js not found. Install from https://nodejs.org/"; exit 1 

$npmCli = "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js"
Set-Location "$PSScriptRoot\frontend"

# Install if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    & $node $npmCli install --legacy-peer-deps
}

Write-Host "Starting frontend on http://localhost:5173 ..."
& $node $npmCli run dev
