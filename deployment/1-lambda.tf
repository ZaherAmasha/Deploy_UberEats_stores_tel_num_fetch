
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
    function_name = "prod_UberEats_phone_number_fetch_lambda"
    role = aws_iam_role.iam_for_lambda.arn
    description = <<EOF
        Gets a batch of stores from DynamoDB, fetches 
        their phone numbers using the Google Places API, packages the data into a Google Sheet and sends it to a channel in Slack
    EOF

    source_code_hash = data.archive_file.lambda.output_base64sha256
    handler = "main.lambda_handler"
    runtime = "python3.11"
    layers = [aws_lambda_layer_version.python_site_packages_layer.arn]
    timeout = 600 # 600 seconds = 10 minutes
    memory_size  = 256 # to be fine-tuned later
    timeouts {
        create = "20m"
        update = "20m"
    }
    environment {
        variables = {
            GOOGLE_PLACES_API_KEY = var.GOOGLE_PLACES_API_KEY
            LOG_LEVEL = var.LOG_LEVEL
            SLACK_TOKEN = var.SLACK_TOKEN
            SLACK_CHANNEL_ID = var.SLACK_CHANNEL_ID
        }
    }
}
