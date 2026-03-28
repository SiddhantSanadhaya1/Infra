/**
 * Aurora PostgreSQL connection pool
 * Credentials fetched from AWS Secrets Manager at startup.
 * Connection routed through the private subnet to the Aurora cluster endpoint.
 *
 * AWS services used:
 *   - aws_rds_cluster        (aurora-postgresql endpoint)
 *   - aws_secretsmanager_secret (db-credentials)
 *   - aws_security_group.db  (port 5432 ingress from app SG)
 */

const { Pool } = require('pg');
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

const secretsClient = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-east-1' });

let pool = null;

async function getDbCredentials() {
  const secretArn = process.env.DB_SECRET_ARN;
  const cmd = new GetSecretValueCommand({ SecretId: secretArn });
  const response = await secretsClient.send(cmd);
  return JSON.parse(response.SecretString);
}

async function initDatabase() {
  const creds = await getDbCredentials();

  pool = new Pool({
    host:     process.env.DB_ENDPOINT,   // aurora cluster endpoint
    port:     5432,
    database: process.env.DB_NAME || 'appdb',
    user:     creds.username,
    password: creds.password,
    max:      10,
    idleTimeoutMillis: 30000,
    ssl: { rejectUnauthorized: false },
  });

  pool.on('error', (err) => {
    console.error('Unexpected PostgreSQL pool error', err);
  });

  console.log('Aurora PostgreSQL pool initialised');
  return pool;
}

function getPool() {
  if (!pool) throw new Error('Database not initialised — call initDatabase() first');
  return pool;
}

module.exports = { initDatabase, getPool };
