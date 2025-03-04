# Deploy_UberEats_stores_tel_num_fetch

An AWS workflow that takes a batch of scraped stores from a Dynamodb table, fetches their phone numbers using the Google Places API, populates a Google Sheet with the aggregated data, sends the sheet to a Slack channel, and finally updates the status of the items to processed in the Dynamodb table with the obtained phone numbers.

## Video Demo

Coming soon!!

## Project Overview

This project creates an automated pipeline to extract phone numbers for UberEats store listings in the UK. The pipeline works as follows:

1. Pre-scraped UberEats store data is stored in a DynamoDB table
2. A Lambda function is triggered 4 times per month via EventBridge
3. The Lambda processes batches of 1000 stores at a time
4. For each store, the Google Places API is queried to find the store's phone number
5. Results are compiled into a Google Sheet
6. The Google Sheet is shared to a Slack channel
7. Store records in DynamoDB are updated with phone numbers and marked as processed

The data stored in the DynamoDB table was scraped earlier from the UberEats website by reverse engineering the website's backend APIs. The data scraped is publicly available on the website. The scraping was done politely over the span of 3 days to avoid putting significant load on the UberEats backend servers. The scraped data and scraping methodology are not shared in this repository to preserve the privacy of UberEats and the stores' owners.

The project involves scraping approximately 150,000 UberEats store listings across the UK, collecting comprehensive data on restaurants, cafes, and food establishments.

The scraped stores represent all listings in the UK present on the UberEats website, organized by city/area. For each store, the store name, store address, rating, area/city, and description were extracted. Phone numbers are not available on the UberEats website (part of their strategy to keep customers in-app for orders).

## Business Objective

The objective of this project is to identify potential leads in the food service industry (restaurants, cafes, diners, etc.). UberEats has compiled a database of high-quality leads on their platform. By extracting this data and obtaining phone numbers, businesses can reach out to these establishments directly.

The automated pipeline gets the phone numbers and packages them into Google Sheets that are:
1. Shared in a specified Slack channel
2. Stored in an admin-access Google Drive folder
3. Accumulated since deployment

To get the phone numbers of individual stores, the text search capability of Google Places API is used, querying with the name and address of individual stores. This is equivalent to searching Google Maps for each particular store and extracting the phone numbers.


## Prerequisites

Before deploying this project, you'll need:

1. **AWS Account** with permissions to create:
   - Lambda functions
   - EventBridge schedules
   - DynamoDB tables
   - Systems Manager Parameter Store entries
   - IAM roles and policies
   - S3 buckets

2. **Google Cloud Account** with the following APIs enabled:
   - Places API
   - Google Drive API
   - Google Sheets API
   - A service account with appropriate permissions

3. **Slack Workspace** with:
   - Admin permissions to create a Slack app
   - A dedicated channel for receiving Google Sheets

4. **Local Development Environment** with:
   - Terraform (≥ v1.0.0)
   - Python (≥ 3.8)
   - AWS CLI configured with appropriate credentials
   - Git

## AWS Required Services Diagram

A high-level overview of the pipeline.

![high level deployment diagram](/assets/high_level_deployment_diagram.png)

## Pipeline Workflow Steps

Activity Diagram showing the logical workflow of the pipeline.

![activity diagram](/assets/pipeline_workflow_steps.png)


## Some Technical Implementation Details

### DynamoDB Optimization
A Global Secondary Index (GSI) was created on the `status` attribute in the DynamoDB table. This allows for:
- Efficient querying of stores based on their processing status
- Avoiding full table scans
- Significantly improved query performance

### Data Modeling
A Pydantic data model was implemented for individual stores, providing:
- Strong type checking
- Validation of store data
- Consistent data structure throughout the pipeline
- Simplified data manipulation and transfer between different components of the system

### API Interaction Strategy
The solution implements advanced API interaction techniques for the Google Places API:
- Asynchronous API calls to improve overall pipeline performance
- Carefully managed rate limiting (600 requests per minute)
- Sophisticated error handling with:
  - Exponential back-off mechanism
  - Jitter to prevent request thundering herd problem
  - Robust handling of 'Too many requests' exceptions
- Ensures respectful and efficient API interaction


## Project Structure

```
├── assets                          # Diagrams and images
│   └── high_level_deployment_diagram.png
│   └── pipeline_workflow_steps.png
│   └── workflow_diagram.md         # PlantUML diagram for the pipeline_workflow_steps.png
├── data                            # Scraped data
│   └── store.csv
├── deployment                      # Terraform deployment files
│   ├── 0-provider.tf               # AWS provider configuration
│   ├── 1-lambda.tf                 # Lambda function definition
│   ├── 2-eventbridge.tf            # EventBridge schedule configuration
│   ├── 3-dynamodb.tf               # DynamoDB table definition
│   ├── 4-SSM_gcp_credentials.tf    # Systems Manager Parameter Store setup
│   ├── scripts                     # Deployment scripts
│   │   ├── package.sh              # Script to prepare Lambda dependencies
│   │   └── upload_dataset_to_dynamodb.py  # Script to populate DynamoDB
│   └── variables.tf                # Terraform variables
├── src                             # Source code
│   ├── main.py                     # Lambda handler
│   ├── google_places_api.py        # Google Places API client
│   ├── models                      # Data models
│   │   └── store.py
│   ├── slack_bot                   # Slack integration
│   │   └── bot.py
│   └── utils                       # Utility functions
│       ├── common_utils.py
│       ├── dynamodb_utils.py
│       ├── google_sheet_utils.py
│       └── logger.py
├── s3_terraform_backend_setup      # S3 backend setup for Terraform state
│   └── main.tf
├── .github                         # Github Actions workflow for terraform
|   └── workflows
|       └── terraform.yml           
├── .gitignore                      
├── .env                            # Environment variables
├── .env.example                    # Example environment variables
├── google_credentials.json         # Google credentials
├── LICENSE
├── README.md
└── requirements.txt                # Python dependencies
```

## Terraform Configuration Used to Deploy

The Infrastructure as Code (IaC) tool Terraform is used to provision the required AWS resources. The project is split into 3 main deployment steps:

### 1. S3 Bucket for Terraform State

The `s3_terraform_backend_setup` directory contains Terraform code to provision an S3 bucket to store the Terraform state, with state locking enabled to prevent more than a single entity from modifying the state simultaneously. This is run only once, before provisioning the rest of the resources.

```bash
cd s3_terraform_backend_setup
terraform init
terraform apply
```

### 2. Main Infrastructure Deployment

The `deployment` directory contains the Terraform code that provisions the required main services like Lambda, EventBridge, DynamoDB, Systems Manager Parameter Store, etc. The Terraform state for this pipeline is stored in the S3 bucket created earlier. This is the bulk of the Terraform code.

A GitHub Actions workflow is used to manage the entire deployment pipeline, which includes multiple steps beyond just `terraform apply`, ensuring a comprehensive and automated deployment process.

You can still chose to deploy from your local machine using:

```bash
cd deployment
source ./scripts/package.sh
terraform init
terraform apply
```

### 3. Data Upload

The `deployment/scripts/upload_dataset_to_dynamodb.py` Python script uploads the scraped data into DynamoDB by adding a unique UUID `store_id` for each store and the other needed attributes. It also sets the Global Secondary Index (GSI) `status` for all the stores to `pending`. This is run after provisioning the main pipeline to populate the DynamoDB table.
Use the virtual environment's python interpreter to run this file, more details about the virtual environment down below.
```bash
<use the virtual environment python interpreter> deployment/scripts/upload_dataset_to_dynamodb.py
```

## Deployment Process

To speed up development iterations (due to a relatively slow local internet upload speed), a GitHub Actions workflow is used to provision the main Terraform pipeline when triggered manually in the GitHub Web UI. This workflow:

1. Creates the `.env` file in the context of the github actions workflow, by retrieving from the github repo's secrets.
2. Creates the `google_credentials.json` file using a similar fashion. 
3. Packages all the needed third-party libraries in the Lambda function as a Lambda layer
4. Declares secrets to be passed to AWS as environment variables with the prefix `TF_VAR_`
5. Provisions the main pipeline services with `terraform apply`

Steps 3 and 4 are done by the `package.sh` file.

Since the Terraform state is stored remotely in S3, you can run `terraform destroy` locally to destroy the resources during development. Terraform fetches the state from S3 and uses it to see which resources are being deployed with the specific configuration. Using the native feature of Terraform state locking with S3, you are not allowed to run `terraform destroy` while the GitHub Actions workflow is still running and provisioning the resources, preventing race conditions.

## Environment Variables

A `.env.example` file is provided in the repository as a template for configuring environment variables. To use the project:

Copy `.env.example` to `.env`
Fill in the actual values for each variable:

```bash
cp .env.example .env
```
Edit the .env file and replace the placeholder values with your actual credentials:

* `GOOGLE_PLACES_API_KEY`: Your Google Places API key

* `LOG_LEVEL`: Logging verbosity (e.g., DEBUG, INFO, WARNING)

* `SLACK_TOKEN`: OAuth token for your Slack app

* `SLACK_CHANNEL_ID`: ID of the Slack channel for notifications

* `GOOGLE_DRIVE_FOLDER_ID`: ID of the Google Drive folder for storing sheets

**Note:** Ensure there is an empty line at the end of the `.env` file to prevent errors in the `package.sh` script.

**Important:** Never commit your `.env` file with real credentials to version control. The `.env` file is already included in `.gitignore` to prevent accidental commits.

## Github Secrets

To use the Github Actions workflow to deploy the project, you need to add the following secrets to your GitHub repository:

* `AWS_ACCESS_KEY_ID`: The AWS_ACCESS_KEY_ID for the AWS account used to deploy

* `AWS_SECRET_ACCESS_KEY`: The AWS_SECRET_ACCESS_KEY for the AWS account used to deploy

* `AWS_REGION`: The AWS_REGION for the AWS account used to deploy

* `ENV_FILE_CONTENTS`: The contents of the `.env` file as a single string. The workflow will create the `.env` file from this content.

* `GOOGLE_CREDENTIALS_JSON`: The contents of the `google_credentials.json` file as a single string. The workflow will create the `google_credentials.json` file similarly.



## Setup Instructions

### 1. AWS Setup

1. Install the AWS CLI and configure it with your credentials:
   ```bash
   aws configure
   ```

2. Create the S3 bucket for Terraform state:
   ```bash
   cd s3_terraform_backend_setup
   terraform init
   terraform apply
   ```

### 2. Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Places API
   - Google Drive API
   - Google Sheets API
4. Create a service account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name your service account
   - Grant it the necessary roles ("Editor" for simplicity)
   - Click "Create" and continue
5. Create and download a JSON key:
   - Click on the service account email
   - Navigate to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select JSON format and click "Create"
   - Save the downloaded file as `google_credentials.json` in the project root

6. Set up Google Drive folder:
   - Create a new folder in Google Drive
   - Right-click the folder and select "Share"
   - Share it with the service account email (with Editor permissions)
   - Copy the folder ID from the URL (the part after `folders/` in the URL)
   - Add this ID to your `.env` file as `GOOGLE_DRIVE_FOLDER_ID`

### 3. Slack Setup

1. Go to [https://api.slack.com](https://api.slack.com) and sign in to your workspace
2. Click "Create an App" > "From scratch"
3. Name your app and select your workspace
4. Under "Add features and functionality", click "Permissions"
5. Under "Scopes" > "Bot Token Scopes", add the `chat:write` permission
6. Click "Install to Workspace" at the top of the page
7. Copy the "Bot User OAuth Token" and add it to your `.env` file as `SLACK_TOKEN`
8. Create a channel in your workspace for receiving the Google Sheets
9. Get the channel ID (right-click on the channel, select "Copy link", the ID is the part after the last `/`)
10. Add this ID to your `.env` file as `SLACK_CHANNEL_ID`

### 4. Deploy the Project

1. Create Virtual environment (for dev purposes):
    ```bash
    python3 -m venv .venv
    source .venv/bin/active  # for Linux
    .venv/Scripts/activate   # for Windows
    ```
2. Install Python dependencies (for dev purposes):
   ```bash
   pip install -r requirements.txt
   ```
3. Deploy the infrastructure (2 possible ways):

    3.1. Using GitHub Actions Workflow (Cleanest and fastest way. Recommended):

        Just manually trigger the workflow from GitHub

    3.2. Using Local Machine:

        ```bash
        cd deployment
        source ./scripts/package.sh
        terraform init
        terraform apply
        ```

3. Upload the dataset to DynamoDB:
   ```bash
   <use the virtual environment python interpreter> deployment/scripts/upload_dataset_to_dynamodb.py
   ```

## IAM Role and Security

A restrictive approach was taken in assigning IAM roles and permissions to services, following the AWS security best-practices of using the principle of least privilege. The Lambda function has only the permissions it needs to perform its specific tasks.

## Monitoring and Logging

The application uses CloudWatch Logs for monitoring Lambda function execution. The LOG_LEVEL environment variable controls the verbosity of logging. Set it to DEBUG for more detailed logs during development.

## Limitations

1. The Google Places API has a limit on the number of free requests per month, which is why the pipeline is scheduled to run only 4 times a month
2. The accuracy of phone number matching depends on how well the store names and addresses match between UberEats and Google Places. To mitigate this, a constructed URL to Google Maps with each store's name and address is also stored in the Google Sheet. The user would manually get the phone number using Google Maps using this URL, in case Google Places API does not return a phone number.

## Future Improvements

1. Add a web interface for viewing and managing the extracted data
2. Set up automated alerting for pipeline failures

## Contributing

Contributions to this project are welcome. Please fork the repository, make your changes, and submit a pull request.

## License

Distributed under the Apache-2.0 License. See `LICENSE` file for more information.


