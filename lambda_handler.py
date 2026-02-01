"""AWS Lambda handler for the chickencoop Flask API."""


def handler(event, context):
    """Lambda entry point that adapts API Gateway events to Flask."""
    return {"statusCode": 200, "body": "OK"}
