/**
 * User management routes — CRUD backed by Aurora PostgreSQL.
 * Session validated via DynamoDB + Redis.
 *
 * AWS services used:
 *   - aws_rds_cluster.main             (PostgreSQL reads/writes)
 *   - aws_dynamodb_table.sessions      (session lookup via auth middleware)
 *   - aws_elasticache_replication_group.redis (session cache)
 *   - aws_sqs_queue.main               (async notification jobs)
 *   - aws_lb_target_group.app          (ALB routes /api/users here)
 */

const express  = require('express');
const { getPool } = require('../config/database');
const { requireAuth } = require('../middleware/auth');
const { enqueue } = require('../services/queueService');
const cache = require('../services/cacheService');

const router = express.Router();

// GET /api/users — list users (cached in Redis)
router.get('/', requireAuth, async (req, res) => {
  const cacheKey = 'users:list';
  let users = await cache.get(cacheKey);

  if (!users) {
    const result = await getPool().query('SELECT id, email, name, created_at FROM users ORDER BY created_at DESC LIMIT 100');
    users = result.rows;
    await cache.set(cacheKey, users, 60);
  }

  res.json(users);
});

// GET /api/users/:id
router.get('/:id', requireAuth, async (req, res) => {
  const result = await getPool().query('SELECT id, email, name, created_at FROM users WHERE id = $1', [req.params.id]);
  if (!result.rows.length) return res.status(404).json({ error: 'User not found' });
  res.json(result.rows[0]);
});

// POST /api/users — create user
router.post('/', async (req, res) => {
  const { email, name, password_hash } = req.body;
  const result = await getPool().query(
    'INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3) RETURNING id, email, name, created_at',
    [email, name, password_hash]
  );
  const user = result.rows[0];

  // Fire welcome email job asynchronously
  await enqueue('SEND_WELCOME_EMAIL', { userId: user.id, email: user.email });

  res.status(201).json(user);
});

// DELETE /api/users/:id
router.delete('/:id', requireAuth, async (req, res) => {
  await getPool().query('DELETE FROM users WHERE id = $1', [req.params.id]);
  await cache.del('users:list');
  res.status(204).send();
});

module.exports = router;
