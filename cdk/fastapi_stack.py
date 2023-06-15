import os

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk import Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route53
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct


AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
HOSTED_ZONE_NAME = os.environ.get("HOSTED_ZONE_NAME", "indexhub.ai")
HOSTED_ZONE_ID = os.environ.get("HOSTED_ZONE_ID", "Z036403337CGSDN2VWQ2C")
APP_DNS_NAME = os.environ.get("APP_DNS_NAME", "api.indexhub.ai")
CERTIFICATE_ARN = os.environ.get(
    "CERTIFICATE_ARN",
    "arn:aws:acm:us-west-2:472617627528:certificate/32f09b92-f755-4d85-bac7-cd55bb8a3541",
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
            cluster_name="indexhub-ecs-cluster-v2",
            vpc=self.vpc,
            # enable_fargate_capacity_providers=True,
            # container_insights=True
        )

        # Get hosted zone and certificate (created from AWS console)
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=HOSTED_ZONE_ID,
            zone_name=HOSTED_ZONE_NAME,
        )
        cert = acm.Certificate.from_certificate_arn(
            self, "SubdomainCertificate", CERTIFICATE_ARN
        )

        # SECRETS
        psql_secret = Secret.from_secret_name_v2(
            self, "PostgresSecret", secret_name="prod/indexhub/postgres"
        )
        modal_secret = Secret.from_secret_name_v2(
            self, "ModalSecret", secret_name="prod/indexhub/modal"
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
                    resources=[psql_secret.secret_arn, modal_secret.secret_arn],
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
                        "arn:aws:s3:::indexhub-public-trends",
                        "arn:aws:s3:::indexhub-public-trends/*",
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
                    resources=["*"]
                    # resources=[
                    #     f"arn:aws:secretsmanager:{AWS_DEFAULT_REGION}:{AWS_ACCOUNT_ID}:secret:prod/storage/*",
                    #     f"arn:aws:secretsmanager:{AWS_DEFAULT_REGION}:{AWS_ACCOUNT_ID}:secret:prod/sources/*"
                    # ],
                    # conditions={
                    #     "StringNotEquals": {"aws:ResourceTag/owner": "indexhub"},
                    #     "StringEquals": {"aws:ResourceTag/owner": "user"},
                    # },
                ),
            ],
            roles=[task_role],
        )

        # ECS Task
        image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_asset(
                directory=".",
                file="indexhub/Dockerfile",
                follow_symlinks=cdk.SymlinkFollowMode.ALWAYS,
            ),
            container_port=8000,
            environment={
                "ENV_NAME": "prod",
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
                "MODAL_TOKEN_ID": ecs.Secret.from_secrets_manager(modal_secret, "id"),
                "MODAL_TOKEN_SECRET": ecs.Secret.from_secrets_manager(
                    modal_secret, "secret"
                ),
            },
            execution_role=execution_role,
            task_role=task_role,
        )

        self.ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "IndexHubFastAPIService",
            cluster=self.ecs_cluster,
            cpu=2048,
            memory_limit_mib=8192,
            desired_count=1,
            certificate=cert,
            domain_name=APP_DNS_NAME,
            domain_zone=hosted_zone,
            task_image_options=image_options,
            public_load_balancer=True,
            redirect_http=True,
            health_check_grace_period=Duration.seconds(150),
        )

        # Retrieve the target group
        target_group = self.ecs_service.target_group
        # Change the success codes
        target_group.configure_health_check(path="/", healthy_http_codes="200,403")
