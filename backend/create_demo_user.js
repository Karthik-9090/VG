(async () => {
  const auth = require('./services/authService');
  try {
    const res = await auth.register('demo@vayuguard.com','Demo@123','Demo User');
    console.log(JSON.stringify({status: 'ok', result: res}));
  } catch (e) {
    console.error(JSON.stringify({status:'error', message: e.message, code: e.statusCode || null}));
    process.exit(1);
  }
})();
