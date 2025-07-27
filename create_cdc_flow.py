#!/usr/bin/env python3
"""
NiFi CDC Flow Creator
Creates a CDC flow in NiFi using the API based on configuration files
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from nifi_api_client import NiFiAPIClient
from config_parser import ConfigParser
from cdc_flow_builder import CDCFlowBuilder


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Create CDC flow in NiFi")
    parser.add_argument(
        "mapping",
        help="Mapping name (without .properties extension)"
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Base path for configuration files (default: current directory)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    logger = setup_logging(args.log_level)
    
    try:
        # Initialize configuration parser
        logger.info("Initializing configuration parser...")
        config_parser = ConfigParser(args.base_path)
        env_config = config_parser.get_env_config()
        
        # Initialize NiFi API client
        logger.info(f"Connecting to NiFi at {env_config['nifi_api_base_url']}...")
        nifi_client = NiFiAPIClient(
            env_config["nifi_api_base_url"],
            env_config["nifi_api_username"],
            env_config["nifi_api_password"]
        )
        
        # Create CDC flow builder
        logger.info("Creating CDC flow builder...")
        flow_builder = CDCFlowBuilder(config_parser, nifi_client)
        
        # Create the CDC flow
        logger.info(f"Creating CDC flow for mapping: {args.mapping}")
        result = flow_builder.create_cdc_flow(args.mapping)
        
        logger.info("CDC flow created successfully!")
        logger.info(f"Process Group ID: {result['process_group']['id']}")
        logger.info(f"Process Group Name: {result['process_group']['name']}")
        logger.info(f"Number of processors created: {len(result['processors'])}")
        
        print("\n✅ CDC Flow created successfully!")
        print(f"Process Group: {result['process_group']['name']} (ID: {result['process_group']['id']})")
        print("\nProcessors created:")
        for name, processor in result['processors'].items():
            print(f"  - {processor['name']} ({processor['type']})")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error creating CDC flow: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()