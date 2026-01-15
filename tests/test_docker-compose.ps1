
Write-Host "======================================"
Write-Host " MLOps Docker-Compose Integration Test"
Write-Host "======================================"

# ======================================================
# Helper
# ======================================================
function Assert-Ok {
    param (
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "$Name"

    try {
        $result = & $Command
        Write-Host "   OK"
        return $result
    }
    catch {
        Write-Host "   FAILED"
        Write-Host "   Error: $($_.Exception.Message)"
        exit 1
    }
}

# ======================================================
# INFRA
# ======================================================
Write-Host ""
Write-Host "Docker-Compose infrastructure"
Write-Host ""

Assert-Ok "Docker containers running" {
    docker-compose ps
}

# ======================================================
# HEALTH CHECKS
# ======================================================
Write-Host ""
Write-Host "Health check"

Assert-Ok "Gateway health" {
    Invoke-RestMethod http://localhost:8000/health
}
Assert-Ok "inference health" {
    Invoke-RestMethod http://localhost:8001/health
}
Assert-Ok "MLflow health" {
    Invoke-WebRequest http://localhost:5000 -UseBasicParsing
}

# ======================================================
# AUTHENTICATION
# ======================================================
Write-Host ""
Write-Host " Authentication"

$adminToken = Assert-Ok "Admin login" {
    (Invoke-RestMethod `
        -Method POST `
        -Uri http://localhost:8000/token `
        -ContentType "application/x-www-form-urlencoded" `
        -Body "username=admin&password=admin123"
    ).access_token
}

$userToken = Assert-Ok "User login" {
    (Invoke-RestMethod `
        -Method POST `
        -Uri http://localhost:8000/token `
        -ContentType "application/x-www-form-urlencoded" `
        -Body "username=user&password=user123"
    ).access_token
}

# ======================================================
# TRAINING
# ======================================================
Write-Host ""
Write-Host " Training"

Assert-Ok "Train SVM (admin)" {
    $response = Invoke-WebRequest `
        -Method POST `
        -Uri http://localhost:8000/train/svm `
        -Headers @{ Authorization = "Bearer $adminToken" }

    if ($response.StatusCode -notin 200, 202) {
        throw "Unexpected status code: $($response.StatusCode)"
    }

    $response.StatusCode
}

Assert-Ok "Train CNN (admin)" {
    $response = Invoke-WebRequest `
        -Method POST `
        -Uri http://localhost:8000/train/cnn `
        -Headers @{ Authorization = "Bearer $adminToken" }

    if ($response.StatusCode -notin 200, 202) {
        throw "Unexpected status code: $($response.StatusCode)"
    }

    $response.StatusCode
}

# ======================================================
# INFERENCE
# ======================================================
Write-Host ""
Write-Host "Inference"

# ---------- SVM ----------
$bodyText = @{
    text = "console de jeu portable nintendo"
} | ConvertTo-Json -Depth 3

Assert-Ok "Predict SVM" {
    Invoke-RestMethod `
        -Method POST `
        -Uri http://localhost:8000/predict/svm `
        -Headers @{
            Authorization = "Bearer $userToken"
            "Content-Type" = "application/json"
        } `
        -Body $bodyText
}

# ---------- CNN ----------
$bodyImg = @{
    image_path = "data/raw/image_train/image_528113_product_923222.jpg"
} | ConvertTo-Json -Depth 3

Assert-Ok "Predict CNN" {
    Invoke-RestMethod `
        -Method POST `
        -Uri http://localhost:8000/predict/cnn `
        -Headers @{
            Authorization = "Bearer $userToken"
            "Content-Type" = "application/json"
        } `
        -Body $bodyImg
}

Write-Host ""
Write-Host "======================================"
Write-Host " 🎉 ALL DOCKER-COMPOSE TESTS PASSED"
Write-Host "======================================"
