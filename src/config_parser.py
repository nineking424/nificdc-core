import configparser
from pathlib import Path
from typing import Dict, Any
import os
from dotenv import load_dotenv


class ConfigParser:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        load_dotenv(self.base_path / ".env")
        
    def parse_datasource(self, datasource_name: str) -> Dict[str, Any]:
        """Parse datasource properties file"""
        filepath = self.base_path / "datasources" / f"{datasource_name}.properties"
        
        # Read as simple properties file (not INI format)
        properties = {}
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
        
        return properties
    
    def parse_mapping(self, mapping_name: str) -> Dict[str, Any]:
        """Parse mapping properties file"""
        filepath = self.base_path / "mappings" / f"{mapping_name}.properties"
        
        properties = {}
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
        
        return properties
    
    def get_env_config(self) -> Dict[str, str]:
        """Get environment configuration"""
        return {
            "nifi_api_base_url": os.getenv("NIFI_API_BASE_URL"),
            "nifi_api_username": os.getenv("NIFI_API_USERNAME", ""),
            "nifi_api_password": os.getenv("NIFI_API_PASSWORD", ""),
            "nifi_root_process_group_id": os.getenv("NIFI_ROOT_PROCESS_GROUP_ID", "root"),
            "nifi_cdc_process_group_name": os.getenv("NIFI_CDC_PROCESS_GROUP_NAME", "CDC-Flows")
        }
    
    def build_jdbc_url(self, db_properties: Dict[str, str]) -> str:
        """Build JDBC URL from database properties"""
        db_type = db_properties.get("db.type", "oracle")
        
        if db_type == "oracle":
            host = db_properties.get("db.host")
            port = db_properties.get("db.port")
            service_name = db_properties.get("db.service.name")
            return f"jdbc:oracle:thin:@{host}:{port}:{service_name}"
        
        # Add other database types as needed
        return ""