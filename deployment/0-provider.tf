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
    
    backend "s3" {
        bucket = "uber-eats-project-terraform-state"
        key = "terraform.tfstate"
        region = "us-east-1"
    }
}

provider "aws" {
    region = "us-east-1"
}
