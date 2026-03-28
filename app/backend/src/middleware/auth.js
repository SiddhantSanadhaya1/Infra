/**
 * Session-based auth middleware.
 * Validates session token from cookie against DynamoDB session store.
 *
 * AWS services used:
 *   - aws_dynamodb_table.sessions (via sessionService)
 *   - aws_elasticache_replication_group.redis (session cache, via cacheService)
 */

const { getSession } = require('../services/sessionService');
const cache = require('../services/cacheService');

async function requireAuth(req, res, next) {
  const sessionId = req.cookies?.session_id;
  if (!sessionId) return res.status(401).json({ error: 'No session' });

  // Check Redis cache first to avoid DynamoDB lookup on every request
  const cacheKey = `session:${sessionId}`;
  let session = await cache.get(cacheKey);

  if (!session) {
    session = await getSession(sessionId);
    if (session) await cache.set(cacheKey, session, 60);
  }

  if (!session) return res.status(401).json({ error: 'Invalid or expired session' });

  req.user = { id: session.user_id };
  next();
}

module.exports = { requireAuth };
