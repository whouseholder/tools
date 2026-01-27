"""
Cloudera Machine Learning Model Deployment Script

This script automates the deployment of the Text-to-SQL agent
as a CML Model using the CML API.
"""

import os
import sys
import time
from pathlib import Path

import cmlapi
from cmlapi.rest import ApiException
from loguru import logger


def get_cml_client():
    """
    Create and return a CML API client.
    
    Requires environment variables:
        - CML_API_KEY: Your CML API key
        - CML_HOST: CML workspace host (e.g., ml-xxxxx.cml.company.com)
    """
    api_key = os.environ.get("CML_API_KEY")
    host = os.environ.get("CML_HOST")
    
    if not api_key or not host:
        raise ValueError(
            "CML_API_KEY and CML_HOST environment variables must be set.\n"
            "Get your API key from: CML UI -> User Settings -> API Keys"
        )
    
    # Create client
    client = cmlapi.default_client(
        url=f"https://{host}",
        cml_api_key=api_key
    )
    
    return client


def create_model(client, project_id: str, model_name: str = "text-to-sql-agent"):
    """
    Create a new model in CML.
    
    Args:
        client: CML API client
        project_id: CML project ID
        model_name: Name for the model
    
    Returns:
        Created model object
    """
    logger.info(f"Creating model: {model_name}")
    
    try:
        model_request = cmlapi.CreateModelRequest(
            name=model_name,
            description="Text-to-SQL Agent for natural language query generation",
            project_id=project_id,
            disable_authentication=False  # Enable authentication
        )
        
        model = client.create_model(
            body=model_request,
            project_id=project_id
        )
        
        logger.info(f"Model created: {model.id}")
        return model
        
    except ApiException as e:
        logger.error(f"Failed to create model: {e}")
        raise


def create_model_build(
    client,
    project_id: str,
    model_id: str,
    runtime_identifier: str = "docker.repository.cloudera.com/cloudera/cdsw/ml-runtime-workbench-python3.9-standard:2023.12.1-b8",
    requirements_path: str = "cloudera/cml_requirements.txt"
):
    """
    Create a model build.
    
    Args:
        client: CML API client
        project_id: CML project ID
        model_id: Model ID
        runtime_identifier: CML runtime identifier
        requirements_path: Path to requirements file
    
    Returns:
        Model build object
    """
    logger.info("Creating model build...")
    
    try:
        build_request = cmlapi.CreateModelBuildRequest(
            project_id=project_id,
            model_id=model_id,
            comment="Initial build with Text-to-SQL agent",
            file_path="cloudera/cml_model.py",
            function_name="predict",
            kernel="python3",
            runtime_identifier=runtime_identifier
        )
        
        build = client.create_model_build(
            body=build_request,
            project_id=project_id,
            model_id=model_id
        )
        
        logger.info(f"Build created: {build.id}")
        
        # Wait for build to complete
        logger.info("Waiting for build to complete...")
        max_wait = 600  # 10 minutes
        start_time = time.time()
        
        while True:
            build = client.get_model_build(
                project_id=project_id,
                model_id=model_id,
                build_id=build.id
            )
            
            if build.status in ["built", "failed"]:
                break
            
            if time.time() - start_time > max_wait:
                raise TimeoutError("Build timed out after 10 minutes")
            
            time.sleep(10)
        
        if build.status == "failed":
            raise RuntimeError(f"Build failed: {build.built_at}")
        
        logger.info("Build completed successfully")
        return build
        
    except ApiException as e:
        logger.error(f"Failed to create build: {e}")
        raise


def create_model_deployment(
    client,
    project_id: str,
    model_id: str,
    build_id: str,
    cpu: float = 2.0,
    memory: int = 4,
    replicas: int = 1
):
    """
    Create a model deployment.
    
    Args:
        client: CML API client
        project_id: CML project ID
        model_id: Model ID
        build_id: Build ID
        cpu: CPU cores
        memory: Memory in GB
        replicas: Number of replicas
    
    Returns:
        Model deployment object
    """
    logger.info("Creating model deployment...")
    
    try:
        deployment_request = cmlapi.CreateModelDeploymentRequest(
            project_id=project_id,
            model_id=model_id,
            build_id=build_id,
            cpu=cpu,
            memory=memory,
            replicas=replicas
        )
        
        deployment = client.create_model_deployment(
            body=deployment_request,
            project_id=project_id,
            model_id=model_id,
            build_id=build_id
        )
        
        logger.info(f"Deployment created: {deployment.id}")
        
        # Wait for deployment to be ready
        logger.info("Waiting for deployment to be ready...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while True:
            deployment = client.get_model_deployment(
                project_id=project_id,
                model_id=model_id,
                build_id=build_id,
                deployment_id=deployment.id
            )
            
            if deployment.status in ["deployed", "failed"]:
                break
            
            if time.time() - start_time > max_wait:
                raise TimeoutError("Deployment timed out after 5 minutes")
            
            time.sleep(10)
        
        if deployment.status == "failed":
            raise RuntimeError("Deployment failed")
        
        logger.info("Deployment ready")
        return deployment
        
    except ApiException as e:
        logger.error(f"Failed to create deployment: {e}")
        raise


def deploy_model(
    project_id: str,
    model_name: str = "text-to-sql-agent",
    cpu: float = 2.0,
    memory: int = 4,
    replicas: int = 1
):
    """
    Main function to deploy the Text-to-SQL agent as a CML Model.
    
    Args:
        project_id: CML project ID
        model_name: Name for the model
        cpu: CPU cores
        memory: Memory in GB
        replicas: Number of replicas
    
    Returns:
        Dictionary with deployment details
    """
    logger.info("Starting CML Model deployment")
    logger.info(f"Project ID: {project_id}")
    
    # Get CML client
    client = get_cml_client()
    
    # Create model
    model = create_model(client, project_id, model_name)
    
    # Create build
    build = create_model_build(client, project_id, model.id)
    
    # Create deployment
    deployment = create_model_deployment(
        client, project_id, model.id, build.id,
        cpu=cpu, memory=memory, replicas=replicas
    )
    
    # Get access key for API calls
    access_key = deployment.access_key
    
    logger.info("=" * 60)
    logger.info("Deployment successful!")
    logger.info("=" * 60)
    logger.info(f"Model ID: {model.id}")
    logger.info(f"Build ID: {build.id}")
    logger.info(f"Deployment ID: {deployment.id}")
    logger.info(f"Access Key: {access_key}")
    logger.info("=" * 60)
    
    return {
        "model_id": model.id,
        "build_id": build.id,
        "deployment_id": deployment.id,
        "access_key": access_key,
        "endpoint": f"https://{os.environ.get('CML_HOST')}/model"
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy Text-to-SQL Agent to CML"
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="CML Project ID"
    )
    parser.add_argument(
        "--model-name",
        default="text-to-sql-agent",
        help="Model name (default: text-to-sql-agent)"
    )
    parser.add_argument(
        "--cpu",
        type=float,
        default=2.0,
        help="CPU cores (default: 2.0)"
    )
    parser.add_argument(
        "--memory",
        type=int,
        default=4,
        help="Memory in GB (default: 4)"
    )
    parser.add_argument(
        "--replicas",
        type=int,
        default=1,
        help="Number of replicas (default: 1)"
    )
    
    args = parser.parse_args()
    
    try:
        result = deploy_model(
            project_id=args.project_id,
            model_name=args.model_name,
            cpu=args.cpu,
            memory=args.memory,
            replicas=args.replicas
        )
        
        print("\n✓ Deployment successful!")
        print(f"\nAccess your model at:")
        print(f"  {result['endpoint']}")
        print(f"\nAccess Key: {result['access_key']}")
        print(f"\nSave this key to call the model API.")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)
