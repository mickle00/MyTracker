import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (aws_lambda as lambda_,
                     aws_lambda_python_alpha as lambda_python,
                     aws_sns_subscriptions as subscriptions,
                     aws_sns as sns,
                     aws_dynamodb as dynamodb,
                     Duration,
                     aws_events as events,
                     aws_events_targets as targets,
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

        rule = events.Rule(self, "DailyRule",
                 schedule=events.Schedule.cron(minute="0", hour="4"),
                )

        rule.add_target(targets.LambdaFunction(handler))

        event_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=['*'], actions=['*'])
        handler.add_to_role_policy(event_policy)
        
        flo_handler = lambda_python.PythonFunction(self, "FloHandler",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    entry="resources",
                    index="monitor_flo.py",
                    handler="main",
                    timeout=Duration.minutes(10),
                    environment = {
                        'FLO_USER': 'mickle00@gmail.com',
                        'DYNAMODB_TABLE': table.table_name
                    }
                    )

        hourly_rule = events.Rule(self, "HourlyRule",
                 schedule=events.Schedule.cron(minute="0"),
                )

        hourly_rule.add_target(targets.LambdaFunction(flo_handler))

        flo_event_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=['*'], actions=['*'])
        flo_handler.add_to_role_policy(flo_event_policy)

        scl_handler = lambda_python.PythonFunction(self, "SclHandler",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    entry="resources",
                    index="Scl2.py",
                    handler="main",
                    timeout=Duration.minutes(10),
                    environment = {
                        'DYNAMODB_TABLE': table.table_name
                    }
                    )

        hourly_rule.add_target(targets.LambdaFunction(scl_handler))

        scl_event_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=['*'], actions=['*'])
        scl_handler.add_to_role_policy(scl_event_policy)
