import json
import boto3

dynamodb_client = boto3.resource('dynamodb') 
validation_table = dynamodb_client.Table('ValidationRequests') 

def lambda_handler(event, context):
    image_name = event['queryStringParameters']['imageName']
    
    response = validation_table.get_item(
        Key={
            'FileName': image_name
        }
    )
    return response['Item']
