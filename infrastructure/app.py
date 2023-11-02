#!/usr/bin/env python3

import os
try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

from aws_cdk import (
    App, CfnOutput, Stack
)

from lib.knowledge_vectordb_infra import KnowledgeVectorDbInfra
from lib.embedding_model_inference_infra import EmbeddingModelInferenceInfra
from lib.llm_application_docker import LLMApplicationDockerInfra
from lib.application_infra import ApplicationInfra


class LLMStreamingStack(Stack):
    def __init__(self, app: App, id: str, project_name:str, instance_type:str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        # project_name = kwargs['project_name']
        opensearch_infra = KnowledgeVectorDbInfra(
            self,
            f'{project_name}KnowledgeVectorDb',
            **kwargs
        )

        em_inference_infra = EmbeddingModelInferenceInfra(
            self,
            f'{project_name}EmbeddingInference',
            project_name = project_name,
            instance_type = instance_type,
            **kwargs
        )

        llm_docker_image = LLMApplicationDockerInfra(
            self,
            f'{project_name}DockerImage',
            **kwargs
        )

        # application_infra = ApplicationInfra(
        #     self,
        #     f'{project_name}Application',
        #     image_uri = llm_docker_image.image_uri,
        #     **kwargs
        # )



app = App()
project_name = app.node.try_get_context("project_name")
instance_type = app.node.try_get_context("instance_type")

llm_stack = LLMStreamingStack(app,
                              f"{project_name}Stack",
                              project_name=project_name,
                              instance_type=instance_type,
                              env=cdk.Environment(account=os.environ['CDK_DEFAULT_ACCOUNT'], 
                                                  region=os.environ['CDK_DEFAULT_REGION'])
                            )

cdk.Tags.of(llm_stack).add('CNRP/PRJ', project_name)
app.synth()




