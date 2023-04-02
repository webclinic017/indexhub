from aws_cdk import Stack
from constructs import Construct

import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)


class FastAPIStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "IndexHubVPC",
            vpc_name="indexhub-vpc",
            max_azs=3,  # default is all AZs in region
            # nat_gateways=1
        )

        self.ecs_cluster = ecs.Cluster(
            self,
            "IndexHubECSCluster",
            cluster_name="indexhub-ecs-cluster",
            vpc=self.vpc,
            # enable_fargate_capacity_providers=True,
            # container_insights=True
        )

        image = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_asset(
                directory="indexhub/Dockerfile",
            ),
            container_port=8000,
            environment={},
        )

        self.ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "IndexHubFastAPIService",
            cluster=self.ecs_cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=2,
            task_image_options=image,
            health_check_grace_period=Duration.seconds(150),
        )
