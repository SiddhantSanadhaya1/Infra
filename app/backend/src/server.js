/**
 * Express application server.
 * Runs inside EC2 instances managed by the Auto Scaling Group,
 * behind the Application Load Balancer.
 *
 * AWS services used (entry point):
 *   - aws_autoscaling_group.app  (EC2 hosts running this process)
 *   - aws_lb.main                (ALB in front)
 *   - aws_lb_listener.https      (TLS termination at ALB)
 *   - aws_iam_instance_profile.app (credentials for AWS SDK calls)
 *   - aws_ecr_repository.app     (Docker image source)
 */

require('dotenv').config();
const express      = require('express');
const cookieParser = require('cookie-parser');
const helmet       = require('helmet');
const cors         = require('cors');

const { initDatabase } = require('./config/database');
const { initRedis }    = require('./config/redis');
const { loadConfig }   = require('./middleware/secrets');

const usersRouter  = require('./routes/users');
const filesRouter  = require('./routes/files');
const healthRouter = require('./routes/health');

const app  = express();
const PORT = process.env.PORT || 8080;

app.use(helmet());
app.use(cors({ origin: process.env.ALLOWED_ORIGIN, credentials: true }));
app.use(express.json({ limit: '1mb' }));
app.use(cookieParser());

app.use('/health',     healthRouter);
app.use('/api/users',  usersRouter);
app.use('/api/files',  filesRouter);

async function start() {
  await loadConfig();
  await initDatabase();
  await initRedis();

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server listening on port ${PORT} (env=${process.env.ENVIRONMENT})`);
  });
}

start().catch((err) => {
  console.error('Fatal startup error:', err);
  process.exit(1);
});
