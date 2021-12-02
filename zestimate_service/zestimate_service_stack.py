from constructs import Construct
from aws_cdk import(aws_lambda as lambda_, Stack)
from . import zestimate_service

class ZestimateServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        zestimate_service.ZestimateService(self, "Zestimates")



