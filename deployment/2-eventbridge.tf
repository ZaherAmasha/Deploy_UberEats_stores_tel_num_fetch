# For triggering the lambda function using EventBridge
# Create the EventBridge rule
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "run-lambda-periodically"
  description         = "Trigger lambda function every 5 minutes"
  # cron job runs on 1, 10, 19 and 28th of each month at 8:35 pm UTC (10:35 pm Beirut). Ensuring it runs only 4 times a month
  # The randomness in the choice of the hour and minute to run the schedule is to avoid synchronization issues
  # refer to this for more info: https://developers.google.com/maps/documentation/places/web-service/web-services-best-practices
  schedule_expression = "cron(35 12 2,11,19,28 * ? *)"
}

# Set the Lambda function as the target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.lambda.arn
}

# Give EventBridge permission to invoke the Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}
