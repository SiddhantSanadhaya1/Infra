/**
 * Redis caching layer wrapping ElastiCache.
 * Used for API response caching and rate-limiting counters.
 *
 * AWS services used:
 *   - aws_elasticache_replication_group.redis (primary endpoint)
 */

const { getRedis } = require('../config/redis');

const DEFAULT_TTL = 300; // 5 minutes

async function get(key) {
  const value = await getRedis().get(key);
  return value ? JSON.parse(value) : null;
}

async function set(key, value, ttl = DEFAULT_TTL) {
  await getRedis().set(key, JSON.stringify(value), { EX: ttl });
}

async function del(key) {
  await getRedis().del(key);
}

async function increment(key, ttl = DEFAULT_TTL) {
  const redis = getRedis();
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, ttl);
  return count;
}

module.exports = { get, set, del, increment };
