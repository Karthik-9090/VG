// Create test users directly in PostgreSQL
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'vayuguard',
  user: process.env.DB_USER || 'vayuguard_user',
  password: process.env.DB_PASSWORD || 'vayuguard_pass',
});

const SALT_ROUNDS = 12;

const testUsers = [
  {
    email: 'admin@vayuguard.com',
    password: 'Admin@123',
    name: 'Admin User',
    role: 'admin'
  },
  {
    email: 'demo@vayuguard.com',
    password: 'Demo@123',
    name: 'Demo User',
    role: 'user'
  },
  {
    email: 'user@vayuguard.com',
    password: 'User@123',
    name: 'Regular User',
    role: 'user'
  }
];

async function createTestUsers() {
  try {
    console.log('[TEST USER SETUP] Creating test users...\n');

    for (const testUser of testUsers) {
      // Check if user exists
      const existing = await pool.query('SELECT id FROM users WHERE email = $1', [testUser.email]);
      
      if (existing.rows.length) {
        console.log(`⚠ User already exists: ${testUser.email}`);
        continue;
      }

      // Hash password
      const passwordHash = await bcrypt.hash(testUser.password, SALT_ROUNDS);

      // Insert user
      const result = await pool.query(
        'INSERT INTO users (email, password_hash, name, role) VALUES ($1, $2, $3, $4) RETURNING id, email, name, role',
        [testUser.email, passwordHash, testUser.name, testUser.role]
      );

      if (result.rows.length) {
        console.log(`✓ Created: ${testUser.email}`);
        console.log(`  Username: ${testUser.email}`);
        console.log(`  Password: ${testUser.password}`);
        console.log(`  Role: ${testUser.role}\n`);
      }
    }

    // Show all users
    console.log('\n[TEST USER SETUP] All users in database:\n');
    const allUsers = await pool.query('SELECT id, email, name, role FROM users ORDER BY id');
    allUsers.rows.forEach(user => {
      console.log(`${user.id}. ${user.email} (${user.role})`);
    });

    console.log('\n[TEST USER SETUP] ✓ Complete');
    process.exit(0);
  } catch (err) {
    console.error('[TEST USER SETUP] ✗ Error:', err.message);
    process.exit(1);
  }
}

createTestUsers();
