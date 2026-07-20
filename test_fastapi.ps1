#!/usr/bin/env pwsh

# Test FastAPI endpoints
$BaseUrl = "http://127.0.0.1:8001"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 1: FastAPI Runtime Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: GET /health
Write-Host "TEST 1: GET /health" -ForegroundColor Green
$headers = @{"Content-Type" = "application/json"}
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method Get -Headers $headers -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json
    Write-Host ""
} catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

# Test 2: POST /forecast
Write-Host "TEST 2: POST /forecast" -ForegroundColor Green
$forecastBody = @{
    city = "Chennai"
    aqi = 85.5
    pm2_5 = 45.0
    pm10 = 120.0
    no2 = 35.0
    so2 = 15.0
    co = 1.5
    o3 = 0.0
} | ConvertTo-Json

Write-Host "Request Payload:" -ForegroundColor Yellow
$forecastBody
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/forecast" -Method Post -Body $forecastBody -Headers $headers -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json
    Write-Host ""
} catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

# Test 3: GET /metrics
Write-Host "TEST 3: GET /metrics" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/metrics" -Method Get -Headers $headers -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json
    Write-Host ""
} catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
