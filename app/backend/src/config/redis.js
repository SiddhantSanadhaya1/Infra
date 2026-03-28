/**
 * ElastiCache Redis client
 * Connects to the primary endpoint of the Redis replication group.
 *
 * AWS services used:
 *   - aws_elasticache_replication_group (primary_endpoint_address)
 *   - aws_security_group.app (app SG allows egress to Redis port 6379)
 */

const { createClient } = require('redis');

let redisClient = null;

async function initRedis() {
  redisClient = createClient({
    socket: {
      host: process.env.REDIS_ENDPOINT,
      port: 6379,
      tls: true,
    },
  });

  redisClient.on('error', (err) => console.error('Redis client error', err));
  redisClient.on('connect', () => console.log('ElastiCache Redis connected'));

  await redisClient.connect();
  return redisClient;
}

function getRedis() {
  if (!redisClient) throw new Error('Redis not initialised — call initRedis() first');
  return redisClient;
}

module.exports = { initRedis, getRedis };
