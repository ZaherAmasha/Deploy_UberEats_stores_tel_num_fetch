# For storing the secrets in System Manager Parameter Store
resource "aws_ssm_parameter" "google_credentials" {
  name = "/UberEatsProject/google_credentials"
  description = "Google JSON Credentials for the Google Sheets API"
  type = "String"
  # Free tier, enough because this is a private project that runs entirely 
  # within the AWS network and doesn't expose a public URL
  tier = "Standard" 
  value = file("../google_credentials.json")
}


# IAM policy for the lambda function to access the google credentials from SSM
resource "aws_iam_policy" "lambda_ssm_policy" {
  name = "LambdaSSMReadPolicy"
  description = "Allows Lambda to read from System Manager Parameter Store"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
        Effect = "Allow"
        Action = [
            "ssm:GetParameter"
        ]
        Resource = [
            aws_ssm_parameter.google_credentials.arn
        ]
    }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_attach" {
  role = aws_iam_role.iam_for_lambda.name # This role is created in the 1-lambda.tf file
  policy_arn = aws_iam_policy.lambda_ssm_policy.arn
}




# Note: This is not the most secure way of storing secrets in AWS, but it's good enough for this use case. This is a practical approach,
# but for a production-grade system, AWS secrets manager or a dedicated KMS-encrypted S3 bucket would be a better solution.
# We could've also stored this credentials JSON file in S3 with server-side encryption for an even less secure solution.
# S3 would require to define IAM policies to protect the credentials while SSM has this built-in. 
# And we can't store the Terraform remote state in System Manager Parameter Store because there's a limit of 4 Kb per key. 
# It's somewhat inconvenient to use both S3 and SSM for this simple workload, but it's not a big deal. For a more complex 
# workload, this should be taken into account to reduce the blast radius.