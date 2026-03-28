/**
 * UserList — fetches and displays users from the backend API.
 * Data originates from Aurora PostgreSQL; responses cached in ElastiCache Redis.
 *
 * AWS services used (indirectly via API):
 *   - aws_lb.main                           (ALB → EC2 ASG)
 *   - aws_rds_cluster.main                  (data source)
 *   - aws_elasticache_replication_group.redis (response cache on backend)
 *   - aws_route53_record.app                (DNS for API base URL)
 */

import { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function UserList() {
  const [users, setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  useEffect(() => {
    api.getUsers()
      .then(setUsers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id) {
    await api.deleteUser(id);
    setUsers((prev) => prev.filter((u) => u.id !== id));
  }

  if (loading) return <p>Loading users from Aurora PostgreSQL…</p>;
  if (error)   return <p className="error">Error: {error}</p>;

  return (
    <table>
      <thead>
        <tr><th>ID</th><th>Email</th><th>Name</th><th>Created</th><th></th></tr>
      </thead>
      <tbody>
        {users.map((u) => (
          <tr key={u.id}>
            <td>{u.id}</td>
            <td>{u.email}</td>
            <td>{u.name}</td>
            <td>{new Date(u.created_at).toLocaleDateString()}</td>
            <td><button onClick={() => handleDelete(u.id)}>Delete</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
