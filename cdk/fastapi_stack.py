import os

import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk import Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct


AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]


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

        # SECRETS
        psql_secret = Secret.from_secret_name_v2(
            self, "Secret", secret_name="prod/indexhub/postgres"
        )

        # EXECUTION ROLE
        execution_role = iam.Role(
            self,
            "ExecutionRole",
            role_name="IndexHubExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )
        iam.Policy(
            self,
            "execution-role-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[f"arn:aws:logs:{AWS_DEFAULT_REGION}:{AWS_ACCOUNT_ID}:*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                    ],
                    resources=[psql_secret.secret_arn],
                ),
            ],
            roles=[execution_role],
        )

        # TASK ROLE
        task_role = iam.Role(
            self,
            "TaskRole",
            role_name="IndexHubTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        iam.Policy(
            self,
            "task-role-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["s3:GetObject", "s3:ListBucket"],
                    resources=[
                        "arn:aws:s3:::indexhub-feature-store",
                        "arn:aws:s3:::indexhub-feature-store/*",
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:CreateSecret",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:PutSecretValue",
                        "secretsmanager:TagResource",
                    ],
                    resources=["*"],
                    conditions={
                        "StringNotEquals": {"aws:ResourceTag/owner": "indexhub"},
                        "StringEquals": {"aws:ResourceTag/owner": "user"},
                    },
                ),
            ],
            roles=[task_role],
        )

        # ECS Task
        image = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_asset(
                directory=".", file="indexhub/Dockerfile"
            ),
            container_port=8000,
            environment={
                "DEBUG": "false",
                "PSQL_SSLMODE": "require",
                "AWS_DEFAULT_REGION": AWS_DEFAULT_REGION,
            },
            secrets={
                "PSQL_DBNAME": ecs.Secret.from_secrets_manager(psql_secret, "dbname"),
                "PSQL_PORT": ecs.Secret.from_secrets_manager(psql_secret, "port"),
                "PSQL_USERNAME": ecs.Secret.from_secrets_manager(
                    psql_secret, "username"
                ),
                "PSQL_PASSWORD": ecs.Secret.from_secrets_manager(
                    psql_secret, "password"
                ),
                "PSQL_HOST": ecs.Secret.from_secrets_manager(psql_secret, "host"),
            },
            execution_role=execution_role,
            task_role=task_role,
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
