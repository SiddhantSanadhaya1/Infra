/**
 * Loads runtime config from SSM Parameter Store at startup.
 * Sensitive values (DB password, API keys) come from Secrets Manager.
 *
 * AWS services used:
 *   - aws_ssm_parameter.app_env      (app config)
 *   - aws_secretsmanager_secret.db_credentials
 *   - aws_kms_key.main               (encryption of both)
 */

const { GetParameterCommand } = require('@aws-sdk/client-ssm');
const { GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');
const { ssm, secrets } = require('../config/aws');

async function loadConfig() {
  const project = process.env.PROJECT_NAME || 'infra-app';
  const env     = process.env.ENVIRONMENT  || 'dev';

  const paramPath = `/${project}/${env}/app-env`;
  const paramResult = await ssm.send(new GetParameterCommand({
    Name:           paramPath,
    WithDecryption: true,
  }));

  console.log(`Loaded SSM param ${paramPath}=${paramResult.Parameter.Value}`);
  return { appEnv: paramResult.Parameter.Value };
}

async function getSecret(secretId) {
  const result = await secrets.send(new GetSecretValueCommand({ SecretId: secretId }));
  return JSON.parse(result.SecretString);
}

module.exports = { loadConfig, getSecret };
