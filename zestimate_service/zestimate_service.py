import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (aws_lambda as lambda_,
                     aws_lambda_python_alpha as lambda_python,
                     aws_iam as iam)


class ZestimateService(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        handler = lambda_python.PythonFunction(self, "ZestimateServiceHandler",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    entry="resources",
                    index="parse.py",
                    handler="main",
                    )

        event_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW, resources=['*'], actions=['*'])
        handler.add_to_role_policy(event_policy)
