/**
 * FileUpload — two-step upload:
 *   1. GET presigned S3 URL from backend (/api/files/presign)
 *   2. PUT file directly to S3 using the presigned URL
 *   3. POST to /api/files to register the upload (triggers Lambda processing job)
 *
 * AWS services used (indirectly via API calls):
 *   - aws_s3_bucket.app              (direct PUT upload target)
 *   - aws_lb.main                    (API calls go through ALB)
 *   - aws_cloudfront_distribution.app (CDN URL returned for display)
 *   - aws_sqs_queue.main             (Lambda job enqueued server-side)
 *   - aws_lambda_function.worker     (processes upload after registration)
 */

import { useState } from 'react';
import { api } from '../services/api';

export default function FileUpload({ onUploaded }) {
  const [status, setStatus] = useState('idle'); // idle | uploading | done | error
  const [cdnUrl, setCdnUrl]  = useState('');

  async function handleChange(e) {
    const file = e.target.files[0];
    if (!file) return;

    setStatus('uploading');
    try {
      // Step 1: get presigned URL from backend (via ALB)
      const { uploadUrl, cdnUrl: url, key } = await api.presignUpload(file.name, file.type);

      // Step 2: upload directly to S3 (bypasses ALB/backend for large files)
      await fetch(uploadUrl, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } });

      // Step 3: notify backend — triggers SQS job → Lambda
      await api.registerFile({ key, filename: file.name, contentType: file.type, size: file.size });

      setCdnUrl(url);
      setStatus('done');
      onUploaded?.({ key, cdnUrl: url });
    } catch (err) {
      setStatus('error');
      console.error('Upload failed:', err);
    }
  }

  return (
    <div className="file-upload">
      <input type="file" onChange={handleChange} disabled={status === 'uploading'} />
      {status === 'uploading' && <p>Uploading to S3…</p>}
      {status === 'done' && (
        <p>
          Uploaded! CDN URL: <a href={cdnUrl} target="_blank" rel="noreferrer">{cdnUrl}</a>
        </p>
      )}
      {status === 'error' && <p className="error">Upload failed — check console</p>}
    </div>
  );
}
