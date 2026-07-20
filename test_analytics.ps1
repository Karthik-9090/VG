#!/usr/bin/env pwsh

# Test analytics endpoints which don't depend on ML service
Write-Host "Testing Analytics Routes (Backend Direct)..." -ForegroundColor Green
Write-Host ""

$baseUrl = "http://127.0.0.1:3000/api"
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzgxNjAxMDA1LCJleHAiOjE3ODE2ODc0MDV9.wCzKxO5hmSDxOUXjz6BitZSSZyDKbZQZnetNgTlo"

$authHeaders = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
}

# Test Analytics Summary
Write-Host "TEST: Analytics Summary" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/analytics/summary" -Method Get -Headers $authHeaders -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host $result
    Write-Host ""
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

# Test Analytics Hotspots
Write-Host "TEST: Analytics Hotspots" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/analytics/hotspots" -Method Get -Headers $authHeaders -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host $result
    Write-Host ""
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}
