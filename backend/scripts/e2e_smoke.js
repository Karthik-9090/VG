const http = require('http');

function check(url) {
  return new Promise((resolve) => {
    http.get(url, (res) => {
      resolve(res.statusCode);
    }).on('error', () => resolve(0));
  });
}

(async () => {
  const urls = [
    'http://localhost:5000/api/health',
    'http://localhost:8001/health',
    'http://localhost:8080/'
  ];
  for (const u of urls) {
    const s = await check(u);
    console.log(u, s);
  }
  process.exit(0);
})();
