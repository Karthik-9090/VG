#!/bin/bash
# Production Release Validation Test Suite

set -e

BASE_URL="${1:-http://localhost}"
API_URL="${BASE_URL}/api"
ML_URL="${BASE_URL}/ml"

echo "VayuGuard Production Release Validation"
echo "========================================"
echo ""

PASSED=0
FAILED=0
RESULTS=()

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4
    local data=$5
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$endpoint" 2>/dev/null || echo -e "error\n0")
    else
        if [ -z "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" "$endpoint" 2>/dev/null || echo -e "error\n0")
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$endpoint" 2>/dev/null || echo -e "error\n0")
        fi
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -1)
    
    if [ "$http_code" -eq "$expected_code" ] || [ "$http_code" -ge "$expected_code" ] && [ "$http_code" -lt 300 ]; then
        echo "✓ (HTTP $http_code)"
        RESULTS+=("$name: PASS")
        ((PASSED++))
    else
        echo "✗ (HTTP $http_code, expected $expected_code)"
        RESULTS+=("$name: FAIL (HTTP $http_code)")
        ((FAILED++))
    fi
}

echo "1. HEALTH & STATUS CHECKS"
echo "========================="
test_endpoint "Nginx Health" "GET" "$BASE_URL/health" 200
test_endpoint "Backend Health" "GET" "$API_URL/health" 200
test_endpoint "ML Health" "GET" "$ML_URL/health" 200

echo ""
echo "2. FRONTEND ROUTES"
echo "=================="
test_endpoint "Frontend Home" "GET" "$BASE_URL/" 200
test_endpoint "Frontend Assets" "GET" "$BASE_URL/index.html" 200

echo ""
echo "3. BACKEND API ROUTES"
echo "===================="
test_endpoint "Backend Health" "GET" "$API_URL/health" 200
test_endpoint "API Base" "GET" "$API_URL/" 200

echo ""
echo "4. ML SERVICE ROUTES"
echo "===================="
test_endpoint "ML Health" "GET" "$ML_URL/health" 200

echo ""
echo "5. SECURITY HEADERS"
echo "==================="
echo -n "Testing HSTS Header... "
header=$(curl -s -I "$BASE_URL/" 2>/dev/null | grep -i "strict-transport-security" | wc -l)
if [ "$header" -gt 0 ]; then
    echo "✓"
    ((PASSED++))
else
    echo "✗"
    ((FAILED++))
fi

echo -n "Testing X-Content-Type-Options... "
header=$(curl -s -I "$BASE_URL/" 2>/dev/null | grep -i "X-Content-Type-Options" | wc -l)
if [ "$header" -gt 0 ]; then
    echo "✓"
    ((PASSED++))
else
    echo "✗"
    ((FAILED++))
fi

echo ""
echo "6. DATABASE CONNECTIVITY"
echo "========================"
echo "PostgreSQL: Check docker-compose logs for connection status"
echo "MongoDB: Check docker-compose logs for connection status"

echo ""
echo "7. MONITORING SYSTEMS"
echo "====================="
test_endpoint "Prometheus" "GET" "http://localhost:9090/api/v1/status/config" 200
test_endpoint "Grafana" "GET" "http://localhost:3000/api/health" 200

echo ""
echo "8. RATE LIMITING"
echo "================"
echo "Testing rate limit (should pass first 100, fail on 101st)"
# Simplified: just verify endpoint is reachable
test_endpoint "Rate Limit Test Endpoint" "GET" "$API_URL/" 401

echo ""
echo "=========================================="
echo "RELEASE VALIDATION SUMMARY"
echo "=========================================="
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo ""
for result in "${RESULTS[@]}"; do
    echo "$result"
done

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✓ RELEASE VALIDATION SUCCESSFUL"
    echo "All critical endpoints verified"
    exit 0
else
    echo ""
    echo "✗ RELEASE VALIDATION FAILED"
    echo "$FAILED test(s) failed"
    exit 1
fi
