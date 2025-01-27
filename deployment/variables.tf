# These are the environment variables exported earlier with the package.sh script. Terraform grabs those
# from the local environment because I prefixed them with TF_VARS_ and has them available when doing 
# terraform apply to be passed to the lambda function

variable "GOOGLE_PLACES_API_KEY" {
  description = "Google Places API Key"
  type        = string
  sensitive = true
}

variable "LOG_LEVEL" {
  description = "Log level for the application"
  type        = string
}

variable "SLACK_TOKEN" {
  description = "Slack Token to be able to send messages"
  type        = string
  sensitive = true
}

variable "SLACK_CHANNEL_ID" {
  description = "Slack Channel ID"
  type        = string
  sensitive = true
}