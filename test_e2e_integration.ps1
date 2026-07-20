#!/usr/bin/env pwsh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 3: Backend Integration Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://127.0.0.1:3000/api"
$headers = @{"Content-Type" = "application/json"}

# Test 1: Register User
Write-Host "TEST 1: Register User" -ForegroundColor Green
$registerBody = @{
    email = "testuser@vayuguard.local"
    password = "TestPassword123!"
    name = "Test User"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/register" -Method Post -Body $registerBody -Headers $headers -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($result | ConvertTo-Json)" -ForegroundColor Green
    Write-Host ""
} catch {
    $err = $_.Exception.Response
    if ($err.StatusCode -eq 400 -or $err.StatusCode -eq 409) {
        Write-Host "User might already exist (expected on rerun)" -ForegroundColor Yellow
    } else {
        Write-Host "FAILED: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Test 2: Login
Write-Host "TEST 2: Login User" -ForegroundColor Green
$loginBody = @{
    email = "testuser@vayuguard.local"
    password = "TestPassword123!"
} | ConvertTo-Json

$token = $null
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method Post -Body $loginBody -Headers $headers -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    $token = $result.token
    Write-Host "Token received: $($token.Substring(0, 20))..." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

if ($token) {
    # Test 3: Make authenticated forecast request
    Write-Host "TEST 3: Forecast Request (with auth)" -ForegroundColor Green
    
    $authHeaders = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    }
    
    $forecastBody = @{
        city = "Chennai"
        horizon = 24
    } | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/forecast" -Method Post -Body $forecastBody -Headers $authHeaders -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response received" -ForegroundColor Green
        Write-Host $result
        Write-Host ""
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            try {
                $errorBody = $_.Exception.Response.GetResponseStream() | ForEach-Object { 
                    $reader = New-Object System.IO.StreamReader($_)
                    $reader.ReadToEnd()
                }
                Write-Host "Error Body: $errorBody" -ForegroundColor Red
            } catch {}
        }
        Write-Host ""
    }
    
    # Test 4: Current AQI
    Write-Host "TEST 4: Current AQI (with auth)" -ForegroundColor Green
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/forecast/current-aqi?city=Bengaluru" -Method Get -Headers $authHeaders -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response received" -ForegroundColor Green
        Write-Host $result
        Write-Host ""
    } catch {
        Write-Host "Expected error (endpoint may not be implemented): $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host ""
    }
}

Write-Host "Integration testing complete" -ForegroundColor Cyan
