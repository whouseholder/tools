"""
Deploy Text-to-SQL Agent to Cloudera AI Inference Service

This script automates deployment to the next-generation CAI platform.
"""

import os
import sys
import yaml
from pathlib import Path
from loguru import logger


def load_deployment_config(config_path: str = "cloudera/ai_inference_config.yaml") -> dict:
    """Load deployment configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def validate_environment():
    """Validate required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "HIVE_HOST",
        "HIVE_USER",
        "HIVE_PASSWORD"
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Set them before deployment."
        )
    
    logger.info("✓ All required environment variables are set")


def create_deployment_manifest(config: dict, output_path: str):
    """
    Create Kubernetes-style deployment manifest for CAI.
    
    Args:
        config: Deployment configuration
        output_path: Path to write manifest
    """
    manifest = {
        "apiVersion": "inference.cloudera.com/v1",
        "kind": "InferenceService",
        "metadata": {
            "name": config["model"]["name"],
            "labels": {
                "app": "text-to-sql-agent",
                "version": config["model"]["version"]
            }
        },
        "spec": {
            "predictor": {
                "custom": {
                    "container": {
                        "name": "predictor",
                        "image": "text-to-sql-agent:latest",
                        "env": [
                            {"name": k, "value": v} 
                            for k, v in config["environment"].items()
                        ],
                        "resources": {
                            "requests": {
                                "cpu": f"{config['resources']['cpu']['default']}",
                                "memory": f"{config['resources']['memory']['default']}Gi"
                            },
                            "limits": {
                                "cpu": f"{config['resources']['cpu']['max']}",
                                "memory": f"{config['resources']['memory']['max']}Gi"
                            }
                        },
                        "volumeMounts": [
                            {
                                "name": vol["name"],
                                "mountPath": vol["path"]
                            }
                            for vol in config["volumes"]
                        ]
                    }
                }
            },
            "scaling": {
                "minReplicas": config["scaling"]["min_replicas"],
                "maxReplicas": config["scaling"]["max_replicas"],
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "targetAverageUtilization": config["scaling"]["target_cpu_utilization"]
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "targetAverageUtilization": config["scaling"]["target_memory_utilization"]
                        }
                    }
                ]
            },
            "volumes": [
                {
                    "name": vol["name"],
                    "persistentVolumeClaim": {
                        "claimName": f"{config['model']['name']}-{vol['name']}"
                    }
                }
                for vol in config["volumes"]
            ]
        }
    }
    
    # Write manifest
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    logger.info(f"✓ Deployment manifest created: {output_path}")
    return manifest


def deploy_to_cai(
    manifest_path: str,
    namespace: str = "default"
):
    """
    Deploy model to Cloudera AI Inference.
    
    Args:
        manifest_path: Path to deployment manifest
        namespace: Kubernetes namespace
    """
    import subprocess
    
    logger.info("Deploying to Cloudera AI Inference...")
    
    # Apply manifest using kubectl
    cmd = [
        "kubectl", "apply",
        "-f", manifest_path,
        "-n", namespace
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Deployment failed: {result.stderr}")
    
    logger.info(f"✓ Deployment successful")
    logger.info(result.stdout)
    
    # Wait for deployment to be ready
    logger.info("Waiting for deployment to be ready...")
    
    model_name = yaml.safe_load(open(manifest_path))["metadata"]["name"]
    
    cmd = [
        "kubectl", "wait",
        "--for=condition=Ready",
        f"inferenceservice/{model_name}",
        "-n", namespace,
        "--timeout=300s"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.warning(f"Deployment may not be ready: {result.stderr}")
    else:
        logger.info("✓ Deployment is ready")


def get_service_url(model_name: str, namespace: str = "default") -> str:
    """
    Get the service URL for the deployed model.
    
    Args:
        model_name: Model name
        namespace: Kubernetes namespace
    
    Returns:
        Service URL
    """
    import subprocess
    
    cmd = [
        "kubectl", "get",
        f"inferenceservice/{model_name}",
        "-n", namespace,
        "-o", "jsonpath='{.status.url}'"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get service URL: {result.stderr}")
    
    url = result.stdout.strip().strip("'")
    return url


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy Text-to-SQL Agent to Cloudera AI Inference"
    )
    parser.add_argument(
        "--config",
        default="cloudera/ai_inference_config.yaml",
        help="Path to deployment config"
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace"
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only generate manifest, don't deploy"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("Text-to-SQL Agent - CAI Deployment")
        logger.info("=" * 60)
        
        # Validate environment
        validate_environment()
        
        # Load config
        config = load_deployment_config(args.config)
        logger.info(f"✓ Loaded config: {args.config}")
        
        # Create manifest
        manifest_path = "cloudera/deployment_manifest.yaml"
        create_deployment_manifest(config, manifest_path)
        
        if args.manifest_only:
            logger.info("Manifest-only mode: skipping deployment")
            logger.info(f"Manifest saved to: {manifest_path}")
            return
        
        # Deploy
        deploy_to_cai(manifest_path, args.namespace)
        
        # Get service URL
        model_name = config["model"]["name"]
        service_url = get_service_url(model_name, args.namespace)
        
        logger.info("=" * 60)
        logger.info("✓ Deployment Complete!")
        logger.info("=" * 60)
        logger.info(f"Model Name: {model_name}")
        logger.info(f"Service URL: {service_url}")
        logger.info("=" * 60)
        
        print("\nNext steps:")
        print("  1. Test your deployment:")
        print(f"     curl -X POST {service_url}/predict \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"inputs\": {\"question\": \"Show top customers\"}}'")
        print("")
        print("  2. Monitor your deployment:")
        print(f"     kubectl logs -f deployment/{model_name} -n {args.namespace}")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
