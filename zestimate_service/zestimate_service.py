import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (aws_lambda as lambda_,
                     aws_lambda_python_alpha as lambda_python,
                     aws_sns_subscriptions as subscriptions,
                     aws_sns as sns,
                     aws_dynamodb as dynamodb,
                     Duration,
                     aws_iam as iam)


class ZestimateService(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        table = dynamodb.Table(self, "ZestimateHistory",
                partition_key=dynamodb.Attribute(name='date', type = dynamodb.AttributeType.STRING),
                sort_key=dynamodb.Attribute(name='timestamp', type = dynamodb.AttributeType.STRING)
                )

        topic = sns.Topic(self, "ZestimateNotifications")
        topic.add_subscription(subscriptions.SmsSubscription("+12069493916"))

        handler = lambda_python.PythonFunction(self, "ZestimateServiceHandler",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    entry="resources",
                    index="parse.py",
                    handler="main",
                    timeout=Duration.minutes(10),
                    environment = {
                        'SNS_TOPIC': topic.topic_arn,
                        'DYNAMODB_TABLE': table.table_name
                    }
                    )

        event_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=['*'], actions=['*'])
        handler.add_to_role_policy(event_policy)



