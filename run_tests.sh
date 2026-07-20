#!/bin/sh
TOKEN=$(cat /tmp/token.txt)
echo ---CURRENT-AQI---
curl -i -s -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/forecast/current-aqi?city=Chennai"
echo

echo ---FORECAST---
curl -i -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "http://localhost:5000/api/forecast" -d '{"city":"Chennai","horizon":24}'
echo

echo ---HEALTH---
curl -i -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "http://localhost:5000/api/forecast/health-risk" -d '{"city":"Chennai","profile":"general","horizon":24}'
