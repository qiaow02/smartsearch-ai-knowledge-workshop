#!/usr/bin/env python3
import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_elasticloadbalancingv2 as elbv2,
    aws_apigatewayv2_integrations_alpha as apigwv2_int,
    aws_apigatewayv2_alpha as apigwv2,
    App, CfnOutput, Stack
)

from constructs import Construct

class ApplicationInfra(Construct):
    
    def __init__(self, scope: Construct, id: str, **kwargs)-> None:
        super().__init__(scope, id)

        image_uri = kwargs['image_uri']
        region = os.environ.get("CDK_DEPLOY_REGION",
                                os.environ["CDK_DEFAULT_REGION"])
    

        data = open("./user_data.sh", "rb").read()
        # httpd.add_commands(str(data,'utf-8'))
        
        user_data = ec2.UserData.for_linux()
        # user_data.add_commands(str(data,'utf-8'))
        # user_data.add_commands(f'docker pull --verbose {image_uri}')
        # docker run --gpus '"device=0"' -p 5000:5000 -it -d --restart=on-failure ${account}.dkr.ecr.${REGION}.amazonaws.com.cn/llm_smart_search:latest
        # user_data.add_commands(f'docker run --gpus \'"device=0"\' -p 5000:5000 -it -d --restart=on-failure {image_uri}')

        print(f'user_data: {user_data.render()}')
        
        # vpc_infra = VPCInfra(
        #     self,
        #     'LLMVPC')
        
        # ec2_role = self._create_ec2_role()

        # asg:autoscaling.AutoScalingGroup = autoscaling.AutoScalingGroup(
        #     self,
        #     "LLMASG",
        #     vpc=vpc_infra.vpc,
        #     instance_type=ec2.InstanceType.of(ec2.InstanceClass.G4DN, ec2.InstanceSize.XLARGE2),
        #     ##todo for gpu? machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
        #     # machine_image=ec2.MachineImage.generic_linux({region:ami_img_id}), # pytorch gpu
        #     machine_image=ec2.MachineImage.latest_amazon_linux(),
        #     block_devices=[autoscaling.BlockDevice(
        #         device_name="/dev/xvda",
        #         volume=autoscaling.BlockDeviceVolume.ebs(50,
        #             volume_type=autoscaling.EbsDeviceVolumeType.GP3,
        #             encrypted = True,
        #             throughput=600,
        #             delete_on_termination=True
        #         )
        #     )
        #     ],
        #     role = ec2_role,
        #     user_data=httpd,
        #     ssm_session_permissions = True,
        #     min_capacity = min_capacity,
        #     max_capacity = max_capacity,
        #     termination_policies= [autoscaling.TerminationPolicy.OLDEST_INSTANCE]
        # )

        # # cdk.Tags.of(asg).add('Patch Group', 'AccountGuardian-PatchGroup-DO-NOT-DELETE')

        # lb = elbv2.ApplicationLoadBalancer(
        #     self, "LLM-ALB",
        #     vpc=vpc_infra.vpc,
        #     internet_facing=True,
        #     load_balancer_name='LLM-ALB')

        # listener = lb.add_listener("Listener", port=1080, protocol=elbv2.ApplicationProtocol.HTTP)
        # listener.add_targets("Target", port=5000, protocol=elbv2.ApplicationProtocol.HTTP, targets=[asg])
        # listener.connections.allow_default_port_from_any_ipv4("Open to the world")

        # asg.scale_on_request_count("AModestLoad", target_requests_per_minute=60)
        # CfnOutput(self,"LoadBalancer",export_name="LLMLoadBalancer",value=f'{lb.load_balancer_dns_name}:1080/summarize')
    
    def _create_ec2_role(self):
        # EC2 IAM Roles
        name = "Ec2"
        ec2_role = iam.Role(
            self,
            f"{name}Role",
            description="LLM EC2 Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:SetRepositoryPolicy",
                                "ecr:CompleteLayerUpload",
                                "ecr:BatchDeleteImage",
                                "ec2:CreateVpcEndpoint",
                                "ec2:DescribeRouteTables",
                                "cloudwatch:PutMetricData",
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:GetLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "iam:ListRoles",
                                "iam:GetRole",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "Ec2RoleName", value=ec2_role.role_name)

        return ec2_role

class VPCInfra(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id)

        self._scope = scope

        self._vpc = ec2.Vpc(
            self,
            "LLMVPC",
            max_azs=3,
            ip_addresses= ec2.IpAddresses.cidr("172.31.100.0/22"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24,
                ),
            ]
        )

        # add flow log
        self._vpc.add_flow_log("FlowLogVPC")

    @property
    def subnet_selection(self):
        return self._vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets

    @property
    def vpc(self):
        return self._vpc

    @property
    def vpc_endpoint(self):
        return self._vpc.endpoint_id

class LLMStreamingStack(Stack):
    def _create_ec2_role(self):
        # EC2 IAM Roles
        name = "Ec2"
        ec2_role = iam.Role(
            self,
            f"{name}Role",
            description="LLM EC2 Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy(
                    self,
                    f"{name}Policy",
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:SetRepositoryPolicy",
                                "ecr:CompleteLayerUpload",
                                "ecr:BatchDeleteImage",
                                "ec2:CreateVpcEndpoint",
                                "ec2:DescribeRouteTables",
                                "cloudwatch:PutMetricData",
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:GetLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "iam:ListRoles",
                                "iam:GetRole",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "Ec2RoleName", value=ec2_role.role_name)

        return ec2_role
    
    def __init__(self, app: App, id: str, **kwargs) -> None:
        super().__init__(app, id)

        region = os.environ.get("CDK_DEPLOY_REGION",
                                os.environ["CDK_DEFAULT_REGION"])
        min_capacity = kwargs['min_capacity']
        max_capacity = kwargs['max_capacity']
        ami_img_id = kwargs['ami_img_id']

        # VPC
        vpc_infra = VPCInfra(
            self,
            'LLMVPC')

        data = open("./httpd.sh", "rb").read()
        httpd=ec2.UserData.for_linux()
        httpd.add_commands(str(data,'utf-8'))

        
        ec2_role = self._create_ec2_role()

        asg = autoscaling.AutoScalingGroup(
            self,
            "LLMASG",
            vpc=vpc_infra.vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.G4DN, ec2.InstanceSize.XLARGE2),
            ##todo for gpu? machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            machine_image=ec2.MachineImage.generic_linux({region:ami_img_id}), # pytorch gpu
            block_devices=[autoscaling.BlockDevice(
                device_name="/dev/xvda",
                volume=autoscaling.BlockDeviceVolume.ebs(120,
                    volume_type=autoscaling.EbsDeviceVolumeType.GP3,
                    encrypted = True,
                    throughput=600,
                    delete_on_termination=True
                )
            )
            ],
            role = ec2_role,
            user_data=httpd,
            ssm_session_permissions = True,
            min_capacity = min_capacity,
            max_capacity = max_capacity,
            termination_policies= [autoscaling.TerminationPolicy.OLDEST_INSTANCE]
        )

        cdk.Tags.of(asg).add('Patch Group', 'AccountGuardian-PatchGroup-DO-NOT-DELETE')

        lb = elbv2.ApplicationLoadBalancer(
            self, "LLM-ALB",
            vpc=vpc_infra.vpc,
            internet_facing=True,
            load_balancer_name='LLM-ALB')

        listener = lb.add_listener("Listener", port=1080, protocol=elbv2.ApplicationProtocol.HTTP)
        listener.add_targets("Target", port=5000, protocol=elbv2.ApplicationProtocol.HTTP, targets=[asg])
        listener.connections.allow_default_port_from_any_ipv4("Open to the world")

        asg.scale_on_request_count("AModestLoad", target_requests_per_minute=60)
        CfnOutput(self,"LoadBalancer",export_name="LLMLoadBalancer",value=f'{lb.load_balancer_dns_name}:1080/summarize')
