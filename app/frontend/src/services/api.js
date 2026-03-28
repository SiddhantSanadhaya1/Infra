/**
 * API client — all requests go to the ALB DNS name.
 * In production the ALB is fronted by a Route53 alias record.
 *
 * AWS services used:
 *   - aws_lb.main                   (ALB entry point)
 *   - aws_lb_listener.https         (TLS on 443)
 *   - aws_route53_record.app        (DNS alias → ALB)
 *   - aws_cloudfront_distribution.app (static assets served from CDN)
 */

const BASE_URL = process.env.REACT_APP_API_URL || '';

async function request(method, path, body = null) {
  const opts = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  // Users
  getUsers:   ()          => request('GET',    '/api/users'),
  getUser:    (id)        => request('GET',    `/api/users/${id}`),
  createUser: (data)      => request('POST',   '/api/users', data),
  deleteUser: (id)        => request('DELETE', `/api/users/${id}`),

  // Files
  presignUpload: (filename, contentType) =>
    request('POST', '/api/files/presign', { filename, contentType }),
  registerFile:  (data) => request('POST',   '/api/files', data),
  deleteFile:    (id)   => request('DELETE', `/api/files/${id}`),

  // Health
  health: () => request('GET', '/health'),
};
