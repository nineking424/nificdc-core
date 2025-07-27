from typing import Dict, Any
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from nifi_api_client import NiFiAPIClient
from config_parser import ConfigParser


class CDCFlowBuilder:
    def __init__(self, config_parser: ConfigParser, nifi_client: NiFiAPIClient):
        self.config_parser = config_parser
        self.nifi_client = nifi_client
        self.env_config = config_parser.get_env_config()
        
    def create_cdc_flow(self, mapping_name: str) -> Dict[str, Any]:
        """Create complete CDC flow based on mapping configuration"""
        # Parse configurations
        mapping_config = self.config_parser.parse_mapping(mapping_name)
        source_ds_name = mapping_config.get("source.datasource")
        target_ds_name = mapping_config.get("target.datasource")
        
        source_config = self.config_parser.parse_datasource(source_ds_name)
        target_config = self.config_parser.parse_datasource(target_ds_name)
        
        # Create process group for CDC
        cdc_group = self._create_cdc_process_group(mapping_config.get("mapping.name", "CDC Flow"))
        process_group_id = cdc_group["id"]
        
        # Create controller services
        source_dbcp = self._create_dbcp_service(process_group_id, f"{source_ds_name}_DBCP", source_config)
        target_dbcp = self._create_dbcp_service(process_group_id, f"{target_ds_name}_DBCP", target_config)
        
        # Enable controller services
        time.sleep(2)  # Wait for services to be created
        self.nifi_client.enable_controller_service(source_dbcp["id"])
        self.nifi_client.enable_controller_service(target_dbcp["id"])
        
        # Create processors
        processors = self._create_cdc_processors(
            process_group_id, 
            mapping_config, 
            source_dbcp["id"], 
            target_dbcp["id"]
        )
        
        # Create connections
        self._create_processor_connections(process_group_id, processors)
        
        # Start processors
        for processor in processors.values():
            self.nifi_client.start_processor(processor["id"])
        
        return {
            "process_group": cdc_group,
            "processors": processors,
            "source_dbcp": source_dbcp,
            "target_dbcp": target_dbcp
        }
    
    def _create_cdc_process_group(self, name: str) -> Dict[str, Any]:
        """Create process group for CDC flow"""
        root_pg_id = self.env_config["nifi_root_process_group_id"]
        result = self.nifi_client.create_process_group(root_pg_id, name)
        return result["component"]
    
    def _create_dbcp_service(self, process_group_id: str, name: str, db_config: Dict[str, str]) -> Dict[str, Any]:
        """Create Database Connection Pool controller service"""
        jdbc_url = self.config_parser.build_jdbc_url(db_config)
        
        properties = {
            "Database Connection URL": jdbc_url,
            "Database Driver Class Name": db_config.get("oracle.driver.class", "oracle.jdbc.OracleDriver"),
            "Database User": db_config.get("db.username"),
            "Password": db_config.get("db.password"),
            "Max Total Connections": db_config.get("db.pool.size", "10")
        }
        
        result = self.nifi_client.create_controller_service(
            process_group_id,
            "org.apache.nifi.dbcp.DBCPConnectionPool",
            name,
            properties
        )
        
        return result["component"]
    
    def _create_cdc_processors(self, process_group_id: str, mapping_config: Dict[str, str], 
                              source_dbcp_id: str, target_dbcp_id: str) -> Dict[str, Any]:
        """Create CDC processors"""
        processors = {}
        
        # 1. ExecuteSQL processor for source data extraction
        source_table = mapping_config.get("source.table")
        cdc_column = mapping_config.get("cdc.column")
        cdc_from = mapping_config.get("cdc.incremental.from")
        cdc_to = mapping_config.get("cdc.incremental.to")
        
        sql_query = f"""
        SELECT * FROM {source_table} 
        WHERE {cdc_column} >= TO_TIMESTAMP('{cdc_from}', 'YYYY-MM-DD HH24:MI:SS')
        AND {cdc_column} <= TO_TIMESTAMP('{cdc_to}', 'YYYY-MM-DD HH24:MI:SS')
        """
        
        processors["extract"] = self.nifi_client.create_processor(
            process_group_id,
            "org.apache.nifi.processors.standard.ExecuteSQL",
            "Extract CDC Data",
            {
                "Database Connection Pooling Service": source_dbcp_id,
                "SQL select query": sql_query,
                "Max Rows Per Flow File": mapping_config.get("cdc.batch.size", "1000")
            },
            {"x": 100, "y": 100}
        )["component"]
        
        # 2. ConvertAvroToJSON processor
        processors["convert"] = self.nifi_client.create_processor(
            process_group_id,
            "org.apache.nifi.processors.kite.ConvertAvroToJSON",
            "Convert to JSON",
            {},
            {"x": 400, "y": 100}
        )["component"]
        
        # 3. ConvertJSONToSQL processor
        target_table = mapping_config.get("target.table")
        processors["convert_sql"] = self.nifi_client.create_processor(
            process_group_id,
            "org.apache.nifi.processors.standard.ConvertJSONToSQL",
            "Convert to SQL",
            {
                "Statement Type": "INSERT",
                "Table Name": target_table,
                "Catalog Name": "",
                "Schema Name": ""
            },
            {"x": 700, "y": 100}
        )["component"]
        
        # 4. PutSQL processor for target data loading
        processors["load"] = self.nifi_client.create_processor(
            process_group_id,
            "org.apache.nifi.processors.standard.PutSQL",
            "Load to Target",
            {
                "JDBC Connection Pool": target_dbcp_id,
                "Batch Size": mapping_config.get("cdc.batch.size", "1000")
            },
            {"x": 1000, "y": 100}
        )["component"]
        
        # 5. LogAttribute processor for errors
        processors["log_error"] = self.nifi_client.create_processor(
            process_group_id,
            "org.apache.nifi.processors.standard.LogAttribute",
            "Log Errors",
            {
                "Log Level": "error",
                "Attributes to Log": ".*"
            },
            {"x": 700, "y": 300}
        )["component"]
        
        return processors
    
    def _create_processor_connections(self, process_group_id: str, processors: Dict[str, Any]):
        """Create connections between processors"""
        # Extract -> Convert
        self.nifi_client.create_connection(
            process_group_id,
            processors["extract"]["id"],
            processors["convert"]["id"],
            ["success"]
        )
        
        # Convert -> ConvertSQL
        self.nifi_client.create_connection(
            process_group_id,
            processors["convert"]["id"],
            processors["convert_sql"]["id"],
            ["success"]
        )
        
        # ConvertSQL -> Load
        self.nifi_client.create_connection(
            process_group_id,
            processors["convert_sql"]["id"],
            processors["load"]["id"],
            ["success"]
        )
        
        # Error connections
        for processor_name in ["extract", "convert", "convert_sql", "load"]:
            if processor_name in processors:
                self.nifi_client.create_connection(
                    process_group_id,
                    processors[processor_name]["id"],
                    processors["log_error"]["id"],
                    ["failure"]
                )