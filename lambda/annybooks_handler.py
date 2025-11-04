import json
import os
import logging
import requests
import boto3
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table_name = os.environ["TABLE_NAME"]
sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)
sns_client = boto3.client("sns")


def notify_slack_and_sns(message: str):
    if slack_webhook_url:
        try:
            response = requests.post(
                slack_webhook_url,
                json={"text": message},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Erreur Slack: {e}")

    if sns_topic_arn:
        try:
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Message=json.dumps({"default": message}),
                MessageStructure="json",
            )
        except Exception as e:
            logger.error(f"Erreur SNS: {e}")


def handler(event, context):
    logger.info(f"Event reçu: {event}")
    http_method = event.get("httpMethod")

    if http_method == "GET":
        book_id = event.get("queryStringParameters", {}).get("id")
        if book_id:
            # Récupérer un livre spécifique
            response = table.get_item(Key={"id": book_id})
            item = response.get("Item")
            if not item:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Livre non trouvé"}),
                    "headers": {"Content-Type": "application/json"},
                }
            notify_slack_and_sns(f"Livre {book_id} consulté")
            return {
                "statusCode": 200,
                "body": json.dumps(item),
                "headers": {"Content-Type": "application/json"},
            }
        else:
            # Récupérer tous les livres
            response = table.scan()
            notify_slack_and_sns("Liste des livres consultée")
            return {
                "statusCode": 200,
                "body": json.dumps(response.get("Items", [])),
                "headers": {"Content-Type": "application/json"},
            }

    elif http_method == "POST":
        data = json.loads(event.get("body", "{}"))
        if "title" not in data or "author" not in data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "title et author requis"}),
                "headers": {"Content-Type": "application/json"},
            }
        data["id"] = str(uuid.uuid4())
        table.put_item(Item=data)
        notify_slack_and_sns(
            f"Nouveau livre ajouté : {data['title']} par {data['author']}"
        )
        return {
            "statusCode": 201,
            "body": json.dumps({"message": "Livre ajouté", "livre": data}),
            "headers": {"Content-Type": "application/json"},
        }
    elif http_method == "DELETE":
        data = json.loads(event.get("body", "{}"))
        if "id" not in data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "id requis"}),
                "headers": {"Content-Type": "application/json"},
            }
        table.delete_item(Key={"id": data["id"]})
        notify_slack_and_sns(f"Livre supprimé : {data['id']}")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Livre {data['id']} supprimé"}),
            "headers": {"Content-Type": "application/json"},
        }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "méthode non supportée"}),
            "headers": {"Content-Type": "application/json"},
        }
