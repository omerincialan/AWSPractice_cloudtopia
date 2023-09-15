import json
import boto3
import uuid
import datetime

BUCKET_NAME = "cloudtopia-images" 
FACE_DETAILS_THRESHOLDS = {"Smile": {"desiredValue": False, "minConfidence": 90}, "Sunglasses": {"desiredValue": False, "minConfidence": 90}, "EyesOpen": {"desiredValue": True, "minConfidence": 90}, "MouthOpen": {"desiredValue": False, "minConfidence": 90}}

rekognition_client = boto3.client('rekognition')

def lambda_handler(event, context):
    
    #Step 1 - Extract File Name from PUT Event
    current_file_name = extract_file_name(event)
    
    #Step 2 - Call Rekognition DetectFaces API
    detect_faces_response = detect_faces(current_file_name)
    print(json.dumps(detect_faces_response))
    
    #Step 3 - Extract face details we care about and their value/confidence
    face_details = extract_face_details(detect_faces_response) #extract the attributes we care about
    
    #Step 4 - Evaluates values and thresholds to determine PASS/FAIL
    face_evaluation_result = evaluate_face(face_details)

    print(face_evaluation_result)

def extract_file_name(event):
    return event["Records"][0]["s3"]["object"]["key"]
    
def detect_faces(file_name):
    return rekognition_client.detect_faces(
    Image={
        'S3Object': {
            'Bucket': BUCKET_NAME,
            'Name': file_name
        }
    },
    Attributes=['ALL']
    )

def extract_face_details(result):
    parsed_response = {} 
    
    face_details = result["FaceDetails"]
    face = face_details[0]
    
    #iterate over all fields we care about and extract the details
    for key, value in FACE_DETAILS_THRESHOLDS.items():
        parsed_response[key] = face[key]
        
    return parsed_response

def evaluate_face(parsed_face_scan):

    evaluation_result = {
        "result": "PASS", #we assume it is a pass unless we prove otherwise
        "failure_reasons": []
    }
    
    for key, value in FACE_DETAILS_THRESHOLDS.items():
        temp_result = True #assume we pass the test
        if parsed_face_scan[key]["Value"] != FACE_DETAILS_THRESHOLDS[key]["desiredValue"]:
            print(f"Expected != Actual. FaceAttribute: {key} has a value: {parsed_face_scan[key]['Value']}, but requires {FACE_DETAILS_THRESHOLDS[key]['desiredValue']}")
            temp_result = False
        if parsed_face_scan[key]["Confidence"] < FACE_DETAILS_THRESHOLDS[key]["minConfidence"]:
            print(f"Confidence is lower than minimum threshold. FaceAttribute: {key} has a confidence value: {parsed_face_scan[key]['Confidence']}, but must be greater than {FACE_DETAILS_THRESHOLDS[key]['minConfidence']}")
            temp_result = False
        
        if temp_result is False:
            evaluation_result["result"] = "FAIL"
            evaluation_result["failure_reasons"].append(key)
    return evaluation_result

