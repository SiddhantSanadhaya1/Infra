/**
 * File upload/download routes backed by S3 + CloudFront.
 * Returns presigned S3 URLs for client-side uploads;
 * serves file URLs through the CloudFront CDN domain.
 *
 * AWS services used:
 *   - aws_s3_bucket.app                 (object storage)
 *   - aws_cloudfront_distribution.app   (CDN serving files)
 *   - aws_sqs_queue.main                (enqueue post-upload processing job)
 *   - aws_rds_cluster.main              (store file metadata)
 *   - aws_lb_target_group.app           (ALB routes /api/files here)
 */

const express = require('express');
const { requireAuth } = require('../middleware/auth');
const storage = require('../services/storageService');
const { enqueue } = require('../services/queueService');
const { getPool } = require('../config/database');

const router = express.Router();

// POST /api/files/presign — get a presigned URL to upload directly to S3
router.post('/presign', requireAuth, async (req, res) => {
  const { filename, contentType } = req.body;
  const key = `uploads/${req.user.id}/${Date.now()}-${filename}`;

  const uploadUrl = await storage.getPresignedUploadUrl(key, contentType);
  const cdnUrl    = storage.getCdnUrl(key);

  res.json({ uploadUrl, cdnUrl, key });
});

// POST /api/files — register file after client-side upload completes
router.post('/', requireAuth, async (req, res) => {
  const { key, filename, contentType, size } = req.body;

  const exists = await storage.fileExists(key);
  if (!exists) return res.status(400).json({ error: 'File not found in S3' });

  const result = await getPool().query(
    'INSERT INTO files (user_id, s3_key, filename, content_type, size_bytes) VALUES ($1,$2,$3,$4,$5) RETURNING *',
    [req.user.id, key, filename, contentType, size]
  );
  const file = result.rows[0];

  // Enqueue virus-scan / thumbnail-generation job for Lambda worker
  await enqueue('PROCESS_UPLOAD', { fileId: file.id, key, contentType });

  res.status(201).json({ ...file, cdnUrl: storage.getCdnUrl(key) });
});

// DELETE /api/files/:id
router.delete('/:id', requireAuth, async (req, res) => {
  const result = await getPool().query('SELECT s3_key FROM files WHERE id=$1 AND user_id=$2', [req.params.id, req.user.id]);
  if (!result.rows.length) return res.status(404).json({ error: 'Not found' });

  await storage.deleteFile(result.rows[0].s3_key);
  await getPool().query('DELETE FROM files WHERE id=$1', [req.params.id]);
  res.status(204).send();
});

module.exports = router;
