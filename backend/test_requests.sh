#!/bin/sh
set -e
TOKEN=$(node /app/login_demo_user.js)
echo "---TOKEN---"
echo "$TOKEN"
echo "---CURRENT AQI---"
curl -s -G -H "Authorization: Bearer $TOKEN" --data-urlencode "city=Chennai" http://localhost:5000/api/forecast/current-aqi

echo "\n---FORECAST (24h)---"
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"city":"Chennai","horizon":24}' http://localhost:5000/api/forecast

echo "\n---HEALTH RISK---"
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"city":"Chennai","profile":"general","horizon":24}' http://localhost:5000/api/forecast/health-risk

echo "\n---ALERTS---"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/alerts

echo "\n---PROFILE---"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/users/me
