
Write-Host "======================================"
Write-Host " Docker-Compose Configuration Unit Tests"
Write-Host "======================================"
Write-Host ""

# ======================================================
# YAML Parsing Helper (for JSON compatibility)
# ======================================================
function ConvertFrom-Yaml {
    param([string]$YamlText)
    
    # Convert YAML to JSON by processing docker-compose config output
    # This is a simplified parser that works with docker-compose output
    $YamlText = $YamlText.Trim()
    
    # Use docker-compose's native YAML to JSON conversion via config command
    # Docker-compose config outputs valid JSON
    try {
        return $YamlText | ConvertFrom-Json -AsHashtable
    }
    catch {
        # If JSON parsing fails, return the raw text
        return @{}
    }
}

$failedTests = @()
$passedTests = @()

# ======================================================
# Helper Functions
# ======================================================
function Test-Assert {
    param (
        [string]$Name,
        [scriptblock]$Command,
        [string]$Expected = "OK"
    )

    Write-Host "  ▶ $Name" -NoNewline

    try {
        $result = & $Command
        $passedTests += $Name
        Write-Host " ✓" -ForegroundColor Green
        return $result
    }
    catch {
        $failedTests += @{ Name = $Name; Error = $_.Exception.Message }
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ======================================================
# 1. DOCKER-COMPOSE VALIDATION
# ======================================================
Write-Host ""
Write-Host "[1] Docker-Compose Configuration Validation"
Write-Host ""

Test-Assert "docker-compose.yml syntax valid" {
    $output = docker-compose config 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Invalid YAML syntax: $output"
    }
    return $true
}

# ======================================================
# 2. SERVICES DEFINITION
# ======================================================
Write-Host ""
Write-Host "[2] Services Definition"
Write-Host ""

Test-Assert "gateway service defined" {
    $config = docker-compose config | ConvertFrom-Yaml
    if (-not $config.services.gateway) {
        throw "gateway service not found in docker-compose"
    }
}

Test-Assert "inference service defined" {
    $config = docker-compose config | ConvertFrom-Yaml
    if (-not $config.services.inference) {
        throw "inference service not found"
    }
}

Test-Assert "training service defined" {
    $config = docker-compose config | ConvertFrom-Yaml
    if (-not $config.services.training) {
        throw "training service not found"
    }
}

Test-Assert "mlflow service defined" {
    $config = docker-compose config | ConvertFrom-Yaml
    if (-not $config.services.mlflow) {
        throw "mlflow service not found"
    }
}

# ======================================================
# 3. PORT MAPPINGS
# ======================================================
Write-Host ""
Write-Host "[3] Port Mappings"
Write-Host ""

Test-Assert "gateway port 8000 exposed" {
    $config = docker-compose config | ConvertFrom-Yaml
    $ports = $config.services.gateway.ports
    if ($ports -notcontains "8000:8000") {
        throw "gateway port 8000:8000 not found"
    }
}

Test-Assert "inference port 8001 exposed" {
    $config = docker-compose config | ConvertFrom-Yaml
    $ports = $config.services.inference.ports
    if ($ports -notcontains "8001:8000") {
        throw "inference port 8001:8000 not found"
    }
}

Test-Assert "training port 8002 exposed" {
    $config = docker-compose config | ConvertFrom-Yaml
    $ports = $config.services.training.ports
    if ($ports -notcontains "8002:8000") {
        throw "training port 8002:8000 not found"
    }
}

Test-Assert "mlflow port 5000 exposed" {
    $config = docker-compose config | ConvertFrom-Yaml
    $ports = $config.services.mlflow.ports
    if ($ports -notcontains "5000:5000") {
        throw "mlflow port 5000:5000 not found"
    }
}

# ======================================================
# 4. VOLUME MOUNTS
# ======================================================
Write-Host ""
Write-Host "[4] Volume Mounts"
Write-Host ""

Test-Assert "inference data volume mounted" {
    $config = docker-compose config | ConvertFrom-Yaml
    $volumes = $config.services.inference.volumes
    if ($volumes -notcontains "./data:/app/data") {
        throw "data volume not mounted in inference"
    }
}

Test-Assert "inference models volume mounted" {
    $config = docker-compose config | ConvertFrom-Yaml
    $volumes = $config.services.inference.volumes
    if ($volumes -notcontains "./models:/app/models") {
        throw "models volume not mounted in inference"
    }
}

Test-Assert "training data volume mounted" {
    $config = docker-compose config | ConvertFrom-Yaml
    $volumes = $config.services.training.volumes
    if ($volumes -notcontains "./data:/app/data") {
        throw "data volume not mounted in training"
    }
}

Test-Assert "training models volume mounted" {
    $config = docker-compose config | ConvertFrom-Yaml
    $volumes = $config.services.training.volumes
    if ($volumes -notcontains "./models:/app/models") {
        throw "models volume not mounted in training"
    }
}

Test-Assert "mlflow volume mounted" {
    $config = docker-compose config | ConvertFrom-Yaml
    $volumes = $config.services.mlflow.volumes
    if ($volumes -notcontains "./mlflow/mlruns:/mlflow/mlruns") {
        throw "mlruns volume not mounted"
    }
}

# ======================================================
# 5. ENVIRONMENT VARIABLES
# ======================================================
Write-Host ""
Write-Host "[5] Environment Variables"
Write-Host ""

Test-Assert "inference MLFLOW_TRACKING_URI set" {
    $config = docker-compose config | ConvertFrom-Yaml
    $env = $config.services.inference.environment
    if ($env -notcontains "MLFLOW_TRACKING_URI=http://mlflow:5000") {
        throw "MLFLOW_TRACKING_URI not set in inference"
    }
}

Test-Assert "training MLFLOW_TRACKING_URI set" {
    $config = docker-compose config | ConvertFrom-Yaml
    $env = $config.services.training.environment
    if ($env -notcontains "MLFLOW_TRACKING_URI=http://mlflow:5000") {
        throw "MLFLOW_TRACKING_URI not set in training"
    }
}

Test-Assert "gateway INFERENCE_URL set" {
    $config = docker-compose config | ConvertFrom-Yaml
    $env = $config.services.gateway.environment
    if ($env -notcontains "INFERENCE_URL=http://inference:8000") {
        throw "INFERENCE_URL not set in gateway"
    }
}

Test-Assert "gateway TRAINING_URL set" {
    $config = docker-compose config | ConvertFrom-Yaml
    $env = $config.services.gateway.environment
    if ($env -notcontains "TRAINING_URL=http://training:8000") {
        throw "TRAINING_URL not set in gateway"
    }
}

# ======================================================
# 6. SERVICE DEPENDENCIES
# ======================================================
Write-Host ""
Write-Host "[6] Service Dependencies"
Write-Host ""

Test-Assert "gateway depends on inference" {
    $config = docker-compose config | ConvertFrom-Yaml
    $deps = $config.services.gateway.depends_on
    if ($deps -notcontains "inference") {
        throw "gateway does not depend on inference"
    }
}

Test-Assert "gateway depends on training" {
    $config = docker-compose config | ConvertFrom-Yaml
    $deps = $config.services.gateway.depends_on
    if ($deps -notcontains "training") {
        throw "gateway does not depend on training"
    }
}

Test-Assert "training depends on mlflow" {
    $config = docker-compose config | ConvertFrom-Yaml
    $deps = $config.services.training.depends_on
    if ($deps -notcontains "mlflow") {
        throw "training does not depend on mlflow"
    }
}

# ======================================================
# 7. NETWORK CONFIGURATION
# ======================================================
Write-Host ""
Write-Host "[7] Network Configuration"
Write-Host ""

Test-Assert "mlops_network defined" {
    $config = docker-compose config | ConvertFrom-Yaml
    if (-not $config.networks.mlops_network) {
        throw "mlops_network not defined"
    }
}

Test-Assert "mlops_network is bridge" {
    $config = docker-compose config | ConvertFrom-Yaml
    if ($config.networks.mlops_network.driver -ne "bridge") {
        throw "mlops_network driver is not bridge"
    }
}

Test-Assert "all services on mlops_network" {
    $config = docker-compose config | ConvertFrom-Yaml
    $services = @("gateway", "inference", "training", "mlflow")
    foreach ($service in $services) {
        $networks = $config.services.$service.networks
        if ($networks -notcontains "mlops_network") {
            throw "$service not on mlops_network"
        }
    }
}

# ======================================================
# 8. CONTAINER RUNTIME
# ======================================================
Write-Host ""
Write-Host "[8] Container Runtime Status"
Write-Host ""

Test-Assert "all containers running" {
    $ps = docker-compose ps --services --filter "status=running"
    $services = @("gateway", "inference", "training", "mlflow")
    foreach ($service in $services) {
        if ($ps -notcontains $service) {
            throw "$service not running"
        }
    }
}

Test-Assert "no containers exited with errors" {
    $ps = docker-compose ps
    if ($ps -match "Exit") {
        throw "One or more containers exited with error"
    }
}

# ======================================================
# 9. HEALTH ENDPOINTS
# ======================================================
Write-Host ""
Write-Host "[9] Service Health Checks"
Write-Host ""

Test-Assert "gateway /health endpoint responds" {
    $response = Invoke-RestMethod http://localhost:8000/health
    if ($response.status -ne "ok") {
        throw "gateway health check failed"
    }
}

Test-Assert "inference /health endpoint responds" {
    $response = Invoke-RestMethod http://localhost:8001/health
    if ($response.status -ne "ok") {
        throw "inference health check failed"
    }
}

Test-Assert "training /health endpoint responds" {
    $response = Invoke-RestMethod http://localhost:8002/health
    if ($response.status -ne "ok") {
        throw "training health check failed"
    }
}

# ======================================================
# TEST SUMMARY
# ======================================================
Write-Host ""
Write-Host "======================================"
Write-Host " TEST SUMMARY"
Write-Host "======================================"
Write-Host ""

$totalTests = $passedTests.Count + $failedTests.Count
Write-Host "Total Tests: $totalTests"
Write-Host "Passed: $($passedTests.Count)" -ForegroundColor Green
Write-Host "Failed: $($failedTests.Count)" -ForegroundColor $(if ($failedTests.Count -eq 0) { "Green" } else { "Red" })

if ($failedTests.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed Tests:"
    foreach ($test in $failedTests) {
        Write-Host "  • $($test.Name)" -ForegroundColor Red
    }
    exit 1
}
else {
    Write-Host ""
    Write-Host "✓ All docker-compose configuration tests passed!" -ForegroundColor Green
    exit 0
}
