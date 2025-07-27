import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cdc_flow_builder import CDCFlowBuilder
from config_parser import ConfigParser
from nifi_api_client import NiFiAPIClient


class TestCDCFlowBuilder:
    
    @pytest.fixture
    def mock_config_parser(self):
        """Create mock config parser"""
        mock_parser = Mock(spec=ConfigParser)
        
        # Mock environment config
        mock_parser.get_env_config.return_value = {
            "nifi_api_base_url": "http://test-nifi:8080/nifi-api",
            "nifi_api_username": "test_user",
            "nifi_api_password": "test_pass",
            "nifi_root_process_group_id": "root",
            "nifi_cdc_process_group_name": "CDC-Flows"
        }
        
        # Mock mapping config
        mock_parser.parse_mapping.return_value = {
            "mapping.name": "Test Oracle to Oracle CDC",
            "source.datasource": "test_source",
            "target.datasource": "test_target",
            "source.table": "SCOTT.EMP_1",
            "target.table": "SCOTT.EMP_2",
            "cdc.column": "LAST_UPDATE_TIME",
            "cdc.incremental.from": "2025-07-07 15:00:00",
            "cdc.incremental.to": "2025-07-07 16:00:00",
            "cdc.batch.size": "1000"
        }
        
        # Mock datasource configs
        mock_parser.parse_datasource.side_effect = lambda name: {
            "test_source": {
                "db.type": "oracle",
                "db.host": "192.168.3.13",
                "db.port": "1521",
                "db.service.name": "ORCL",
                "db.username": "scott",
                "db.password": "tiger",
                "oracle.driver.class": "oracle.jdbc.OracleDriver",
                "db.pool.size": "10"
            },
            "test_target": {
                "db.type": "oracle",
                "db.host": "192.168.3.13",
                "db.port": "1521",
                "db.service.name": "ORCL",
                "db.username": "scott",
                "db.password": "tiger",
                "oracle.driver.class": "oracle.jdbc.OracleDriver",
                "db.pool.size": "10"
            }
        }.get(name, {})
        
        # Mock JDBC URL builder
        mock_parser.build_jdbc_url.side_effect = lambda config: "jdbc:oracle:thin:@192.168.3.13:1521:ORCL"
        
        return mock_parser
    
    @pytest.fixture
    def mock_nifi_client(self):
        """Create mock NiFi API client"""
        mock_client = Mock(spec=NiFiAPIClient)
        
        # Mock responses
        mock_client.create_process_group.return_value = {
            "component": {"id": "test-pg-123", "name": "Test CDC Flow"}
        }
        
        mock_client.create_controller_service.side_effect = [
            {"component": {"id": "source-dbcp-456", "name": "test_source_DBCP"}},
            {"component": {"id": "target-dbcp-789", "name": "test_target_DBCP"}}
        ]
        
        mock_client.create_processor.side_effect = [
            {"component": {"id": "extract-proc-111", "name": "Extract CDC Data"}},
            {"component": {"id": "convert-proc-222", "name": "Convert to JSON"}},
            {"component": {"id": "convert-sql-proc-333", "name": "Convert to SQL"}},
            {"component": {"id": "load-proc-444", "name": "Load to Target"}},
            {"component": {"id": "log-proc-555", "name": "Log Errors"}}
        ]
        
        mock_client.create_connection.return_value = {
            "component": {"id": "conn-666"}
        }
        
        return mock_client
    
    @pytest.fixture
    def flow_builder(self, mock_config_parser, mock_nifi_client):
        """Create CDC flow builder with mocks"""
        return CDCFlowBuilder(mock_config_parser, mock_nifi_client)
    
    def test_should_create_complete_cdc_flow(self, flow_builder, mock_config_parser, mock_nifi_client):
        # Act
        with patch('time.sleep'):  # Skip sleep in tests
            result = flow_builder.create_cdc_flow("test_mapping")
        
        # Assert
        assert result["process_group"]["id"] == "test-pg-123"
        assert result["source_dbcp"]["id"] == "source-dbcp-456"
        assert result["target_dbcp"]["id"] == "target-dbcp-789"
        assert len(result["processors"]) == 5
        
        # Verify process group creation
        mock_nifi_client.create_process_group.assert_called_once_with("root", "Test Oracle to Oracle CDC")
        
        # Verify controller services creation
        assert mock_nifi_client.create_controller_service.call_count == 2
        
        # Verify processors creation
        assert mock_nifi_client.create_processor.call_count == 5
        
        # Verify connections creation (3 success + 4 failure connections)
        assert mock_nifi_client.create_connection.call_count == 7
        
        # Verify processors started
        assert mock_nifi_client.start_processor.call_count == 5
    
    def test_should_create_cdc_process_group(self, flow_builder, mock_nifi_client):
        # Act
        result = flow_builder._create_cdc_process_group("Test Group")
        
        # Assert
        assert result["id"] == "test-pg-123"
        mock_nifi_client.create_process_group.assert_called_with("root", "Test Group")
    
    def test_should_create_dbcp_service_with_correct_properties(self, flow_builder, mock_config_parser, mock_nifi_client):
        # Arrange
        db_config = {
            "db.username": "scott",
            "db.password": "tiger",
            "oracle.driver.class": "oracle.jdbc.OracleDriver",
            "db.pool.size": "20"
        }
        
        # Act
        result = flow_builder._create_dbcp_service("test-pg-123", "Test DBCP", db_config)
        
        # Assert
        mock_nifi_client.create_controller_service.assert_called_once()
        call_args = mock_nifi_client.create_controller_service.call_args
        
        assert call_args[0][0] == "test-pg-123"
        assert call_args[0][1] == "org.apache.nifi.dbcp.DBCPConnectionPool"
        assert call_args[0][2] == "Test DBCP"
        
        properties = call_args[0][3]
        assert properties["Database User"] == "scott"
        assert properties["Password"] == "tiger"
        assert properties["Database Driver Class Name"] == "oracle.jdbc.OracleDriver"
        assert properties["Max Total Connections"] == "20"
    
    def test_should_create_cdc_processors_with_correct_configuration(self, flow_builder, mock_nifi_client):
        # Arrange
        mapping_config = {
            "source.table": "EMPLOYEES",
            "target.table": "EMPLOYEES_COPY",
            "cdc.column": "MODIFIED_DATE",
            "cdc.incremental.from": "2024-01-01 00:00:00",
            "cdc.incremental.to": "2024-01-31 23:59:59",
            "cdc.batch.size": "500"
        }
        
        # Act
        processors = flow_builder._create_cdc_processors(
            "test-pg-123",
            mapping_config,
            "source-dbcp-456",
            "target-dbcp-789"
        )
        
        # Assert
        assert len(processors) == 5
        assert "extract" in processors
        assert "convert" in processors
        assert "convert_sql" in processors
        assert "load" in processors
        assert "log_error" in processors
        
        # Verify ExecuteSQL processor configuration
        extract_call = mock_nifi_client.create_processor.call_args_list[0]
        assert extract_call[0][1] == "org.apache.nifi.processors.standard.ExecuteSQL"
        assert "SELECT * FROM EMPLOYEES" in extract_call[0][3]["SQL select query"]
        assert extract_call[0][3]["Max Rows Per Flow File"] == "500"
    
    def test_should_create_processor_connections(self, flow_builder, mock_nifi_client):
        # Arrange
        processors = {
            "extract": {"id": "proc-1"},
            "convert": {"id": "proc-2"},
            "convert_sql": {"id": "proc-3"},
            "load": {"id": "proc-4"},
            "log_error": {"id": "proc-5"}
        }
        
        # Act
        flow_builder._create_processor_connections("test-pg-123", processors)
        
        # Assert
        # Should create 3 success connections + 4 failure connections
        assert mock_nifi_client.create_connection.call_count == 7
        
        # Verify success flow connections
        success_calls = [call for call in mock_nifi_client.create_connection.call_args_list 
                        if call[0][3] == ["success"]]
        assert len(success_calls) == 3
        
        # Verify failure connections
        failure_calls = [call for call in mock_nifi_client.create_connection.call_args_list 
                        if call[0][3] == ["failure"]]
        assert len(failure_calls) == 4
    
    def test_should_handle_missing_mapping_configuration(self, flow_builder, mock_config_parser):
        # Arrange
        mock_config_parser.parse_mapping.return_value = {}
        
        # Act & Assert
        with patch('time.sleep'):
            # The flow will fail when trying to access missing keys
            result = flow_builder.create_cdc_flow("invalid_mapping")
            # Should still return a result but with default name from mocked return
            assert result["process_group"]["name"] == "Test CDC Flow"
    
    def test_should_enable_controller_services(self, flow_builder, mock_nifi_client):
        # Act
        with patch('time.sleep'):
            flow_builder.create_cdc_flow("test_mapping")
        
        # Assert
        # Verify both controller services were enabled
        enable_calls = mock_nifi_client.enable_controller_service.call_args_list
        assert len(enable_calls) == 2
        assert enable_calls[0][0][0] == "source-dbcp-456"
        assert enable_calls[1][0][0] == "target-dbcp-789"
    
    def test_should_start_all_processors(self, flow_builder, mock_nifi_client):
        # Act
        with patch('time.sleep'):
            flow_builder.create_cdc_flow("test_mapping")
        
        # Assert
        start_calls = mock_nifi_client.start_processor.call_args_list
        assert len(start_calls) == 5
        
        # Verify all processor IDs were started
        started_ids = [call[0][0] for call in start_calls]
        expected_ids = [
            "extract-proc-111", "convert-proc-222", "convert-sql-proc-333",
            "load-proc-444", "log-proc-555"
        ]
        for proc_id in expected_ids:
            assert proc_id in started_ids