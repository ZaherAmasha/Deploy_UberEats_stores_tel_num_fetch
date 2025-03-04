```plantuml
@startuml pipeline_workflow_steps

title UberEats Store Phone Number Fetching Pipeline

start
:EventBridge Scheduler;
->Trigger 4 times every month;

partition "Lambda Execution" {
    :Retrieve Google JSON Credentials from SSM;
    :Get a batch of 1000 Unprocessed Stores from DynamoDB;
    :Asynchronously Query Google Places API for the phone numbers of the stores;
    :Create and populate a Google Sheet in the Google Drive Folder;
    :Send the Google Sheet URL to the Slack Channel;
    :Update Store Status of the batch to processed in DynamoDB;
}
:Log Execution Details to CloudWatch Log Group;
stop

@enduml