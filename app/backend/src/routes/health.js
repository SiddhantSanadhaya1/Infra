/**
 * Health check endpoint — checked by the ALB target group every 30s.
 * Returns 200 only when all downstream AWS dependencies are reachable.
 *
 * AWS services used:
 *   - aws_lb_target_group.app        (health_check path = /health)
 *   - aws_rds_cluster.main           (DB ping)
 *   - aws_elasticache_replication_group.redis (Redis ping)
 *   - aws_sqs_queue.main             (queue depth check)
 */

const express = require('express');
const { getPool } = require('../config/database');
const { getRedis } = require('../config/redis');
const { getQueueDepth } = require('../services/queueService');

const router = express.Router();

router.get('/', async (req, res) => {
  const checks = {};
  let healthy = true;

  // Aurora PostgreSQL
  try {
    await getPool().query('SELECT 1');
    checks.postgres = 'ok';
  } catch (e) {
    checks.postgres = `error: ${e.message}`;
    healthy = false;
  }

  // ElastiCache Redis
  try {
    await getRedis().ping();
    checks.redis = 'ok';
  } catch (e) {
    checks.redis = `error: ${e.message}`;
    healthy = false;
  }

  // SQS queue depth (informational — doesn't affect health)
  try {
    checks.sqsDepth = await getQueueDepth();
  } catch (e) {
    checks.sqsDepth = 'unknown';
  }

  res.status(healthy ? 200 : 503).json({ status: healthy ? 'healthy' : 'degraded', checks });
});

module.exports = router;
