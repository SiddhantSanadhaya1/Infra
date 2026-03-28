/**
 * SQS message producer.
 * Publishes jobs to the main queue; the Lambda worker consumes them.
 *
 * AWS services used:
 *   - aws_sqs_queue.main          (job queue)
 *   - aws_sqs_queue.dead_letter   (DLQ for failed messages)
 *   - aws_kms_key.main            (queue encryption)
 *   - aws_lambda_event_source_mapping.sqs_trigger (consumer side)
 */

const { SendMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { sqs } = require('../config/aws');

const QUEUE_URL = process.env.SQS_QUEUE_URL;

async function enqueue(jobType, payload) {
  const body = JSON.stringify({ jobType, payload, enqueuedAt: new Date().toISOString() });

  await sqs.send(new SendMessageCommand({
    QueueUrl:    QUEUE_URL,
    MessageBody: body,
    MessageAttributes: {
      JobType: { DataType: 'String', StringValue: jobType },
    },
  }));

  console.log(`Enqueued job type=${jobType}`);
}

async function getQueueDepth() {
  const result = await sqs.send(new GetQueueAttributesCommand({
    QueueUrl:       QUEUE_URL,
    AttributeNames: ['ApproximateNumberOfMessages'],
  }));
  return parseInt(result.Attributes.ApproximateNumberOfMessages, 10);
}

module.exports = { enqueue, getQueueDepth };
