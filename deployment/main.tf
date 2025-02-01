terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "5.31.0"
        }
        archive = {
            source  = "hashicorp/archive"
            version = "2.4.1"
        }
    }
}

provider "aws" {
    region = "us-east-1"
}

data "aws_iam_policy_document" "assume_role" {
    statement{
        effect = "Allow"
        principals {
            type = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
        actions = ["sts:AssumeRole"]
    }
}

resource "aws_iam_role" "iam_for_lambda" {
    name = "iam_for_lambda"
    assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Add Lambda basic execution role policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_layer_version" "python_site_packages_layer" {
    filename = "site_packages_layer.zip"
    layer_name = "python_site_packages_layer"
    compatible_runtimes = ["python3.11"]
    description = "Layer containing the python packages"
}


data "archive_file" "lambda" {
    type = "zip"
    source_dir = "../src" # for a dir
    output_path = "lambda_function_src.zip"
}

resource "aws_lambda_function" "lambda" {
    filename = "lambda_function_src.zip"
    function_name = "python_terraform_lambda"
    role = aws_iam_role.iam_for_lambda.arn
    
    source_code_hash = data.archive_file.lambda.output_base64sha256
    handler = "main.lambda_handler"
    runtime = "python3.11"
    layers = [aws_lambda_layer_version.python_site_packages_layer.arn]
    timeout = 10
    memory_size  = 128

    environment {
        variables = {
            GOOGLE_PLACES_API_KEY = var.GOOGLE_PLACES_API_KEY
            LOG_LEVEL = var.LOG_LEVEL
            SLACK_TOKEN = var.SLACK_TOKEN
            SLACK_CHANNEL_ID = var.SLACK_CHANNEL_ID
        }
    }
}



# ------------------------------------------------------------------------------------------------
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


# -------------------------------------------------------------------------------------------------
# For storing the store data in DynamoDB
resource "aws_dynamodb_table" "scraped_stores_data"{
    name = "UberEats_scraped_stores_data"
    billing_mode = "PROVISIONED"
    hash_key = "store_id"

    attribute {
        name = "store_id"
        type = "S"
    }
    attribute {
        name = "status"
        type = "S"
    }

    global_secondary_index {
        name = "status-index"
        hash_key = "status"
        projection_type = "ALL"
        read_capacity = 5
        write_capacity = 5
    }

    read_capacity = 5
    write_capacity = 5
}
