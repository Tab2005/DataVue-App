# Start Frontend Service
# DataVue Frontend Development Server

Write-Host "Starting DataVue Frontend..." -ForegroundColor Green

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
    # Change to frontend directory
    Set-Location "$PSScriptRoot\frontend"

    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install npm dependencies" -ForegroundColor Red
            exit 1
        }
    }

    # Verify node/npm are available
    $node = Get-Command node -ErrorAction SilentlyContinue
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $node -or -not $npm) {
        Write-Host "node or npm not found in PATH" -ForegroundColor Red
        exit 1
    }

    # Start the frontend development server in the same window (no new window)
    Write-Host "Starting Vite development server in the same window..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath cmd.exe -ArgumentList '/c', 'npm run dev' -WorkingDirectory "$PSScriptRoot\frontend" -NoNewWindow -PassThru

    # Wait for port 5173
    $ready = 0
    for ($i=0; $i -lt 60; $i++) {
        if (Test-Port -hostname "localhost" -port 5173) { $ready = 1; break }
        Start-Sleep -Seconds 1
    }
    if ($ready -eq 1) {
        Write-Host "Frontend started and listening on port 5173" -ForegroundColor Green
        Write-Host "Frontend running (PID: $($proc.Id))" -ForegroundColor Cyan
        # Keep script alive until user closes this window or presses Ctrl+C
        while (Test-Port -hostname "localhost" -port 5173) { Start-Sleep -Seconds 2 }
    } else {
        Write-Host "Frontend did not become ready within timeout" -ForegroundColor Red
        if ($proc) { Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue }
        exit 1
    }

} catch {
    Write-Host "Error starting frontend: $_" -ForegroundColor Red
    exit 1
}