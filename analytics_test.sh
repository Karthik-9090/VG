#!/bin/sh
TOKEN=$(cat /tmp/token.txt)
echo "---SUMMARY---"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/analytics/summary"; echo "\n---HOTSPOTS---"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/analytics/hotspots"; echo "\n---TRENDS---"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/analytics/trends" > /tmp/trends.json
cat -v /tmp/trends.json
