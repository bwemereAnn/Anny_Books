import json
import os
import logging
import requests
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
table_name = os.environ["TABLE_NAME"]
sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)
sns_client = boto3.client("sns")
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
logger.info("TABLE_NAME:", os.environ.get("TABLE_NAME"))


def notify_slack_and_sns(message: str):
    if SLACK_WEBHOOK_URL:
        try:
            response = requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": message},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.info("Erreur en envoyant sur Slack:", e)

    if SNS_TOPIC_ARN:
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({"default": message}),
                MessageStructure="json",
            )
        except Exception as e:
            logger.info("Erreur en envoyant sur SNS:", e)


def handler(event, context):
    logger.info(f"Event reçu: {event}")
    http_method = event.get("httpMethod")

    if http_method == "GET":
        # http_method récuêre le type de requete
        response = table.scan()
        # table.scan() recupère tous les livres
        notify_slack_and_sns("Liste des livres consultée")
        return {
            "statusCode": 200,
            "body": json.dumps(response["Items"]),
            "headers": {"Content-Type": "application/json"},
        }
    elif http_method == "POST":
        data = json.loads(event.get("body", "{}"))
        logger.info(f"Event reçu: {event}")
        if "id" not in data or "title" not in data or "author" not in data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "id,title et author requis"}),
                "headers": {"Content-Type": "application/json"},
            }
        table.put_item(Item=data)
        # Toujours envoyer statuscode body et headers
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
        logger.info(f"Event reçu: {event}")
        if "id" not in data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "id  requit"}),
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
            "body": json.dumps({"error": "method not supported"}),
            "headers": {"Content-Type": "application/json"},
        }
