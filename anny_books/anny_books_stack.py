from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as _dynamodb,
    RemovalPolicy,
    aws_sns as _sns,
    aws_sns_subscriptions as _sns_subscriptions,
    CfnOutput,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
)


class AnnyBooksStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.table = _dynamodb.Table(
            self,
            "AnnyBooksTable",
            table_name="AnnyBooks",
            partition_key=_dynamodb.Attribute(
                name="id", type=_dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        read_capacity = self.table.metric_consumed_read_capacity_units()
        cloudwatch.Alarm(
            self,
            "HighReadCapacity",
            metric=read_capacity,
            threshold=100,
            evaluation_periods=2,
        )
        alarm_topic = _sns.Topic(
            self, "AnnyBooksTopic", topic_name="AnnyBooksNotification"
        )
        alarm_topic.add_subscription(
            _sns_subscriptions.UrlSubscription(
                "https://hooks.slack.com/services/"
                "T09QHS3MN3W/B09QCA57N14/TRZEgIB0uQBP4KKtWFlW3WJB"
            )
        )

        alarm_topic.metric_number_of_messages_published()
        metric_messages = alarm_topic.metric_number_of_messages_published()
        cloudwatch.Alarm(
            self,
            "ManyMessagesAlarm",
            metric=metric_messages,
            threshold=100,
            evaluation_periods=1,
        )
        lambda_function = _lambda.Function(
            self,
            "AnnyBooksLambdaFunction",
            function_name="AnnyBooksLambdaFunctionCorrection",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="annybooks_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": self.table.table_name,
                "SNS_TOPIC_ARN": alarm_topic.topic_arn,
                "SLACK_WEBHOOK_URL": (
                    "https://hooks.slack.com/services/"
                    "T09QHS3MN3W/B09QCA57N14/TRZEgIB0uQBP4KKtWFlW3WJB"
                ),
            },
        )

        alarm_topic.add_subscription(
            _sns_subscriptions.LambdaSubscription(lambda_function)
        )
        alarm_topic.grant_publish(lambda_function)
        self.table.grant_read_write_data(lambda_function)
        error_metric = lambda_function.metric_errors()
        lambda_error_alarm = cloudwatch.Alarm(
            self,
            "LambdaAnnyBooksErrorAlarm",
            metric=error_metric,
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        api = apigateway.LambdaRestApi(
            self,
            "AnnyBooksAPI",
            rest_api_name="AnnyBooksAPI",
            handler=lambda_function,
            proxy=True,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )
        CfnOutput(self, "TableName", value=self.table.table_name)
        CfnOutput(self, "TopicArn", value=alarm_topic.topic_arn)
        lambda_error_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
        CfnOutput(self, "ApiUrl", value=api.url)

        # https://ve7nv5c1wa.execute-api.eu-north-1.amazonaws.com/prod/
