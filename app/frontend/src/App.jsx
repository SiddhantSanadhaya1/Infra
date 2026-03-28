/**
 * Root React application.
 * Built as a static bundle, uploaded to S3, and served via CloudFront CDN.
 *
 * AWS services used:
 *   - aws_s3_bucket.app                  (static asset storage)
 *   - aws_cloudfront_distribution.app    (global CDN delivery)
 *   - aws_cloudfront_origin_access_control.app (secure S3 access)
 */

import Dashboard from './components/Dashboard';

export default function App() {
  return <Dashboard />;
}
