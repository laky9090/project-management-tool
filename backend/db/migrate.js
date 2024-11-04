const db = require('./connection');
const fs = require('fs').promises;
const path = require('path');

async function applyMigrations() {
  try {
    const migrationFiles = await fs.readdir(path.join(__dirname, 'migrations'));
    
    for (const file of migrationFiles) {
      console.log(`Applying migration: ${file}`);
      const migration = await fs.readFile(
        path.join(__dirname, 'migrations', file),
        'utf-8'
      );
      
      await db.query(migration);
    }
    
    console.log('Migrations completed successfully');
  } catch (err) {
    console.error('Migration failed:', err);
    process.exit(1);
  }
}

if (require.main === module) {
  applyMigrations();
}

module.exports = { applyMigrations };
