/**
 * Session management backed by DynamoDB.
 * Uses the sessions table with TTL on expires_at attribute.
 *
 * AWS services used:
 *   - aws_dynamodb_table.sessions  (hash_key: session_id, TTL: expires_at)
 *   - aws_kms_key.main             (server-side encryption)
 */

const { PutCommand, GetCommand, DeleteCommand } = require('@aws-sdk/lib-dynamodb');
const { dynamo } = require('../config/aws');
const { v4: uuidv4 } = require('uuid');

const TABLE = process.env.DYNAMODB_SESSIONS_TABLE || 'infra-app-dev-sessions';
const SESSION_TTL_SECONDS = 24 * 60 * 60; // 24 hours

async function createSession(userId, metadata = {}) {
  const sessionId = uuidv4();
  const expiresAt = Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS;

  await dynamo.send(new PutCommand({
    TableName: TABLE,
    Item: { session_id: sessionId, user_id: userId, expires_at: expiresAt, ...metadata },
  }));

  return sessionId;
}

async function getSession(sessionId) {
  const result = await dynamo.send(new GetCommand({
    TableName: TABLE,
    Key: { session_id: sessionId },
  }));
  return result.Item || null;
}

async function deleteSession(sessionId) {
  await dynamo.send(new DeleteCommand({
    TableName: TABLE,
    Key: { session_id: sessionId },
  }));
}

module.exports = { createSession, getSession, deleteSession };
