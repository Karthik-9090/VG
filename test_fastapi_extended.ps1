#!/usr/bin/env pwsh

# Extended FastAPI testing for multiple cities and scenarios
$BaseUrl = "http://127.0.0.1:8001"
$headers = @{"Content-Type" = "application/json"}

$testCases = @(
    @{city = "Chennai"; aqi = 85.5; pm2_5 = 45.0; pm10 = 120.0; no2 = 35.0; so2 = 15.0; co = 1.5; o3 = 0.0},
    @{city = "Bengaluru"; aqi = 120.0; pm2_5 = 65.0; pm10 = 150.0; no2 = 42.0; so2 = 20.0; co = 2.0; o3 = 5.0},
    @{city = "Hyderabad"; aqi = 95.0; pm2_5 = 50.0; pm10 = 130.0; no2 = 38.0; so2 = 18.0; co = 1.8; o3 = 2.0}
)

Write-Host "Testing FastAPI /forecast with multiple cities..." -ForegroundColor Cyan
Write-Host ""

foreach ($test in $testCases) {
    $body = $test | ConvertTo-Json
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/forecast" -Method Post -Body $body -Headers $headers -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        Write-Host "PASS: $($test.city): Input AQI $($test.aqi) -> Predicted $($result.forecast_aqi) (v$($result.version))" -ForegroundColor Green
    } catch {
        Write-Host "FAIL: $($test.city): $_" -ForegroundColor Red
    }
}

# Test invalid city
Write-Host ""
Write-Host "Testing invalid city (expected to fail)..." -ForegroundColor Yellow
$invalidBody = @{city = "InvalidCity"; aqi = 50; pm2_5 = 25; pm10 = 60; no2 = 10; so2 = 5; co = 0.5; o3 = 0} | ConvertTo-Json
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/forecast" -Method Post -Body $invalidBody -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "FAIL: Should have failed but didn't" -ForegroundColor Red
}
catch {
    Write-Host "PASS: Correctly rejected invalid city" -ForegroundColor Green
}

Write-Host ""
Write-Host "Comprehensive testing complete" -ForegroundColor Cyan
