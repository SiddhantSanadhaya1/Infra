/**
 * S3 file storage service.
 * Handles presigned URL generation and direct object operations.
 * Files served to users via CloudFront CDN (not directly from S3).
 *
 * AWS services used:
 *   - aws_s3_bucket.app              (versioned, KMS-encrypted asset bucket)
 *   - aws_cloudfront_distribution.app (CDN serving the S3 content)
 *   - aws_kms_key.main               (bucket encryption)
 */

const { PutObjectCommand, DeleteObjectCommand, HeadObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { s3 } = require('../config/aws');

const BUCKET = process.env.S3_BUCKET_NAME;
const CDN_DOMAIN = process.env.CLOUDFRONT_DOMAIN;

async function getPresignedUploadUrl(key, contentType, expiresIn = 300) {
  const url = await getSignedUrl(s3, new PutObjectCommand({
    Bucket: BUCKET,
    Key:    key,
    ContentType: contentType,
    ServerSideEncryption: 'aws:kms',
  }), { expiresIn });
  return url;
}

function getCdnUrl(key) {
  return `https://${CDN_DOMAIN}/${key}`;
}

async function deleteFile(key) {
  await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: key }));
}

async function fileExists(key) {
  try {
    await s3.send(new HeadObjectCommand({ Bucket: BUCKET, Key: key }));
    return true;
  } catch {
    return false;
  }
}

module.exports = { getPresignedUploadUrl, getCdnUrl, deleteFile, fileExists };
