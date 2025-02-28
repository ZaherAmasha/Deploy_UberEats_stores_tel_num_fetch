# For triggering the lambda function using EventBridge
# Create the EventBridge rule
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "run-lambda-periodically"
  description         = "Trigger lambda function every 5 minutes"
  schedule_expression = "rate(5 minutes)" 
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
