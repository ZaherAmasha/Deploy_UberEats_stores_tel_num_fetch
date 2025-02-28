terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "5.31.0"
        }
    }
}

provider "aws" {
    region = "us-east-1"
}


resource "aws_s3_bucket" "terraform_state" {
    bucket = "uber-eats-project-terraform-state"
    lifecycle {
        prevent_destroy = true
    }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id
    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id
    block_public_acls = true
    block_public_policy = true
    ignore_public_acls = true
    restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------
# Create a bucket policy to allow only the account that created the bucket to access it with a restrictive policy
# This gets the root account
data "aws_caller_identity" "current" {}

# This gets the IAM user that is currently logged in and using terraform, here it's called terraform-user
data "aws_iam_session_context" "current" {
    arn = data.aws_caller_identity.current.arn
}

# refer to this for the required permissions: https://developer.hashicorp.com/terraform/language/backend/s3#permissions-required
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "${data.aws_iam_session_context.current.issuer_arn}"
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
        #   "s3:DeleteObject" # The delete is for the lock state file not for the state file
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = "${data.aws_iam_session_context.current.issuer_arn}"
        }
        Action = [
          "s3:ListBucket"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}"
      }
    ]
  })
}


