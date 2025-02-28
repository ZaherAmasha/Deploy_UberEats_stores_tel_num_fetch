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

# Give the Lambda function the permission to access the DynamoDB table
resource "aws_iam_policy" "lambda_dynamodb_policy" {
    name = "LambdaDynamoDBPolicy"
    description = "Allows Lambda to read and write to DynamoDB"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Effect = "Allow"
            Action = [
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:BatchWriteItem",
            ]
            Resource = aws_dynamodb_table.scraped_stores_data.arn
        }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "dynamodb_access" {
    role       = aws_iam_role.iam_for_lambda.name # This role is defined in the 1-lambda.tf file
    policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}