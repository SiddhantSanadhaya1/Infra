/**
 * Dashboard — top-level page component.
 * Static assets (JS bundle, CSS, images) served from CloudFront CDN backed by S3.
 *
 * AWS services used:
 *   - aws_cloudfront_distribution.app  (serves this React bundle)
 *   - aws_s3_bucket.app                (static asset origin)
 *   - aws_lb.main                      (API calls)
 */

import UserList  from './UserList';
import FileUpload from './FileUpload';

export default function Dashboard() {
  return (
    <main>
      <h1>Infra App Dashboard</h1>
      <section>
        <h2>Users</h2>
        <UserList />
      </section>
      <section>
        <h2>File Upload</h2>
        <FileUpload onUploaded={(f) => console.log('Uploaded:', f)} />
      </section>
    </main>
  );
}
