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