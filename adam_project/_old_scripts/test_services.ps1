Write-Host "==============================="
Write-Host " MLOps Platform - microservices tests"
Write-Host "==============================="
Write-Host ""

function Test-Step {
    param (
        [string]$Name,
        [scriptblock]$Command,
        [string]$Expected
    )

    Write-Host " $Name"
    try {
        $result = & $Command
        Write-Host " SUCCESS"
        if ($Expected) {
            Write-Host " Expected: $Expected"
        }
        return $result
    }
    catch {
        Write-Host "  FAILED"
        Write-Host "   Expected: $Expected"
        Write-Host "   Error: $($_.Exception.Message)"
        exit 1
    }
}

# ---------------- INFRA ----------------
Write-Host ""
Write-Host " MLOps Platform - microservices tests - INFRASTRUCTURE"
Write-Host ""

Test-Step `
    "Gateway healthcheck" `
    { Invoke-RestMethod http://127.0.0.1:8000/health } `
    "status=ok"

# ---------------- AUTH ----------------
Write-Host ""
Write-Host " MLOps Platform - microservices tests - AUTHENTIFICATION"
Write-Host ""

Write-Host " ADMIN"
$adminToken = Test-Step `
    "Admin login" `
    {
        (Invoke-RestMethod `
            -Method POST `
            -Uri http://127.0.0.1:8000/token `
            -Headers @{ "Content-Type"="application/x-www-form-urlencoded" } `
            -Body "username=admin&password=admin123"
        ).access_token
    } `
    "JWT token returned"

Write-Host ""
Write-Host " USER"
$userToken = Test-Step `
    "User login" `
    {
        (Invoke-RestMethod `
            -Method POST `
            -Uri http://127.0.0.1:8000/token `
            -Headers @{ "Content-Type"="application/x-www-form-urlencoded" } `
            -Body "username=user&password=user123"
        ).access_token
    } `
    "JWT token returned"

# ---------------- TRAINING ----------------
Write-Host ""
Write-Host " MLOps Platform - microservices tests - TRAINING - admin only"
Write-Host ""

Test-Step `
    "Training via Gateway (admin only)" `
    {
        Invoke-RestMethod `
            -Method POST `
            -Uri http://127.0.0.1:8000/train/svm `
            -Headers @{ Authorization="Bearer $adminToken" }
    } `
    "Model trained + metrics logged in MLflow"

# ---------------- INFERENCE ----------------
Write-Host ""
Write-Host " MLOps Platform - microservices tests - INFERENCE - admin/user"
Write-Host ""
$body = @{ text = "produit est un film de mauvaise qualité" } | ConvertTo-Json -Depth 5

Test-Step `
    "Prediction via Gateway (user)" `
    {
        Invoke-RestMethod `
            -Method POST `
            -Uri http://127.0.0.1:8000/predict `
            -Headers @{
                Authorization="Bearer $userToken"
                "Content-Type"="application/json"
            } `
            -Body $body
    } `
    "predicted_label returned"

# ---------------- SECURITY ----------------
Write-Host ""
Write-Host " MLOps Platform - microservices tests - SECURITY"
Write-Host " training with user status not allowed"
Write-Host ""
Test-Step `
    "Security check: user cannot train" `
    {
        Invoke-RestMethod `
            -Method POST `
            -Uri http://127.0.0.1:8000/train/svm `
            -Headers @{ Authorization="Bearer $userToken" }
    } `
    "403 Forbidden, admin only"


Write-Host ""
Write-Host "==============================="
Write-Host " ALL TESTS PASSED SUCCESSFULLY"
Write-Host "==============================="
