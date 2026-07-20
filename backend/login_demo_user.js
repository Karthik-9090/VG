(async () => {
  const auth = require('./services/authService');
  try {
    const res = await auth.login('demo@vayuguard.com','Demo@123');
    console.log(res.token);
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
})();
