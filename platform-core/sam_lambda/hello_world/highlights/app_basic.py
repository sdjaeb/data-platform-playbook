# Description: Simple AWS Lambda function for local SAM CLI development.
# Source: Highlighting AWS SAM CLI, Basic Use Case.
import json

def lambda_handler(event, context):
    """
    A simple Lambda function to simulate a lightweight ETL step.
    It takes an input event (e.g., a mock transaction) and adds a processing timestamp.
    """
    print("Received event:", json.dumps(event, indent=2))
    try:
        # Assume event body is JSON string for API Gateway proxy integration
        if 'body' in event and isinstance(event['body'], str):
            input_data = json.loads(event['body'])
        else:
            input_data = event # Direct invocation

        # Simulate a lightweight transformation: add a processing timestamp
        if isinstance(input_data, dict):
            # context.get_remaining_time_in_millis() is not available in all local SAM mocks;
            # using a dummy value or current time for broader compatibility.
            input_data['processed_timestamp'] = datetime.utcnow().isoformat() + 'Z' # Using UTC for consistency
            message = "Data processed successfully (local)."
        else:
            message = "Invalid input data format."
            input_data = {} # Ensure input_data is a dict even if invalid

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": message,
                "processed_data": input_data
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except json.JSONDecodeError:
        print("Error: Invalid JSON in event body.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON input"}),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal server error: {e}"}),
            "headers": {
                "Content-Type": "application/json"
            }
        }

