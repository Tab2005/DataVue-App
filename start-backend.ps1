# Start Backend Service
# DataVue Backend Development Server

Write-Host "Starting DataVue Backend..." -ForegroundColor Green

# Function to check if port is open
function Test-Port {
    param($hostname, $port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($hostname, $port)
        $tcpClient.Close()
        return $true
    } catch {
        return $false
    }
}

# Function to wait for service to be ready
function Wait-ForService {
    param($name, $url, $port, $maxWaitSeconds = 30)
    Write-Host "Waiting for $name to be ready at $url..." -ForegroundColor Yellow
    $waited = 0
    while ($waited -lt $maxWaitSeconds) {
        if (Test-Port -hostname "localhost" -port $port) {
            Write-Host "$name is ready!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
        $waited++
    }
    Write-Host "$name failed to start within $maxWaitSeconds seconds" -ForegroundColor Red
    return $false
}

try {
    # Change to backend directory
    Set-Location "$PSScriptRoot\backend"

    # Activate virtual environment (dot-source to affect current session)
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    . .\venv\Scripts\Activate.ps1

    # Verify python is available
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Host "python not found in PATH after activating venv" -ForegroundColor Red
        exit 1
    }

    # Start the backend server as a process so we can monitor port
    Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath python -ArgumentList "main.py" -NoNewWindow -PassThru

    # Wait for port 8000
    $ready = 0
    for ($i=0; $i -lt 60; $i++) {
        if (Test-Port -hostname "localhost" -port 8000) { $ready = 1; break }
        Start-Sleep -Seconds 1
    }
    if ($ready -eq 1) {
        Write-Host "Backend started and listening on port 8000" -ForegroundColor Green
        # Wait for the process to exit (keeps the script alive)
        Wait-Process -Id $proc.Id
    } else {
        Write-Host "Backend did not become ready within timeout" -ForegroundColor Red
        Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
        exit 1
    }

} catch {
    Write-Host "Error starting backend: $_" -ForegroundColor Red
    exit 1
}