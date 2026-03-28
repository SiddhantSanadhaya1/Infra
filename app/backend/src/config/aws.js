/**
 * Shared AWS SDK client instances.
 * EC2 instances use their IAM instance profile for authentication
 * (aws_iam_instance_profile.app → aws_iam_role.app_instance).
 *
 * AWS services used:
 *   - aws_iam_role.app_instance
 *   - aws_iam_instance_profile.app
 *   - aws_iam_role_policy_attachment.ssm
 *   - aws_iam_role_policy_attachment.ecr_readonly
 */

const { S3Client }              = require('@aws-sdk/client-s3');
const { SQSClient }             = require('@aws-sdk/client-sqs');
const { SNSClient }             = require('@aws-sdk/client-sns');
const { DynamoDBClient }        = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');
const { SSMClient }             = require('@aws-sdk/client-ssm');
const { SecretsManagerClient }  = require('@aws-sdk/client-secrets-manager');

const REGION = process.env.AWS_REGION || 'us-east-1';

const s3     = new S3Client({ region: REGION });
const sqs    = new SQSClient({ region: REGION });
const sns    = new SNSClient({ region: REGION });
const dynamo = DynamoDBDocumentClient.from(new DynamoDBClient({ region: REGION }));
const ssm    = new SSMClient({ region: REGION });
const secrets = new SecretsManagerClient({ region: REGION });

module.exports = { s3, sqs, sns, dynamo, ssm, secrets };
