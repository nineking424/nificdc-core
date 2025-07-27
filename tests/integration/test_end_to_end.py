import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import json

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nifi_api_client import NiFiAPIClient
from config_parser import ConfigParser
from cdc_flow_builder import CDCFlowBuilder


class TestEndToEndCDCFlow:
    
    @pytest.fixture
    def test_env_setup(self):
        """Setup test environment variables"""
        test_env = {
            "NIFI_API_BASE_URL": "http://test-nifi:8080/nifi-api",
            "NIFI_API_USERNAME": "test_user",
            "NIFI_API_PASSWORD": "test_pass",
            "NIFI_ROOT_PROCESS_GROUP_ID": "root",
            "NIFI_CDC_PROCESS_GROUP_NAME": "Test-CDC-Flows"
        }
        with patch.dict(os.environ, test_env):
            yield test_env
    
    @pytest.fixture
    def mock_api_responses(self):
        """Create comprehensive mock API responses for full flow"""
        return {
            "process_group": {
                "revision": {"version": 1},
                "component": {
                    "id": "cdc-pg-123",
                    "name": "Test CDC Mapping",
                    "state": "RUNNING"
                }
            },
            "source_dbcp": {
                "revision": {"version": 1},
                "component": {
                    "id": "source-dbcp-456",
                    "name": "test_source_DBCP",
                    "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
                    "state": "ENABLED"
                }
            },
            "target_dbcp": {
                "revision": {"version": 1},
                "component": {
                    "id": "target-dbcp-789",
                    "name": "test_target_DBCP",
                    "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
                    "state": "ENABLED"
                }
            },
            "processors": [
                {
                    "revision": {"version": 1},
                    "component": {
                        "id": "extract-111",
                        "name": "Extract CDC Data",
                        "type": "org.apache.nifi.processors.standard.ExecuteSQL",
                        "state": "RUNNING"
                    }
                },
                {
                    "revision": {"version": 1},
                    "component": {
                        "id": "convert-222",
                        "name": "Convert to JSON",
                        "type": "org.apache.nifi.processors.kite.ConvertAvroToJSON",
                        "state": "RUNNING"
                    }
                },
                {
                    "revision": {"version": 1},
                    "component": {
                        "id": "convert-sql-333",
                        "name": "Convert to SQL",
                        "type": "org.apache.nifi.processors.standard.ConvertJSONToSQL",
                        "state": "RUNNING"
                    }
                },
                {
                    "revision": {"version": 1},
                    "component": {
                        "id": "load-444",
                        "name": "Load to Target",
                        "type": "org.apache.nifi.processors.standard.PutSQL",
                        "state": "RUNNING"
                    }
                },
                {
                    "revision": {"version": 1},
                    "component": {
                        "id": "log-555",
                        "name": "Log Errors",
                        "type": "org.apache.nifi.processors.standard.LogAttribute",
                        "state": "RUNNING"
                    }
                }
            ],
            "connection": {
                "revision": {"version": 1},
                "component": {
                    "id": "conn-999",
                    "selectedRelationships": ["success"]
                }
            }
        }
    
    def test_should_create_complete_cdc_flow_from_config_files(self, test_env_setup, mock_api_responses):
        """Test complete end-to-end CDC flow creation"""
        
        # Setup fixtures path
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_configs"
        
        # Create config parser with test fixtures
        config_parser = ConfigParser(str(fixtures_path))
        
        # Mock NiFi API client
        with patch('requests.Session') as mock_session:
            # Setup authentication response
            auth_response = Mock()
            auth_response.status_code = 201
            auth_response.text = "test-jwt-token"
            
            # Setup API call responses
            mock_session.return_value.post.side_effect = [
                auth_response,  # Authentication
                Mock(json=lambda: mock_api_responses["process_group"], status_code=201),  # Create process group
                Mock(json=lambda: mock_api_responses["source_dbcp"], status_code=201),     # Create source DBCP
                Mock(json=lambda: mock_api_responses["target_dbcp"], status_code=201),     # Create target DBCP
                Mock(json=lambda: mock_api_responses["processors"][0], status_code=201),   # Create extract processor
                Mock(json=lambda: mock_api_responses["processors"][1], status_code=201),   # Create convert processor
                Mock(json=lambda: mock_api_responses["processors"][2], status_code=201),   # Create convert SQL processor
                Mock(json=lambda: mock_api_responses["processors"][3], status_code=201),   # Create load processor
                Mock(json=lambda: mock_api_responses["processors"][4], status_code=201),   # Create log processor
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),      # Create connections (multiple)
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
                Mock(json=lambda: mock_api_responses["connection"], status_code=201),
            ]
            
            # Setup GET responses for enabling services and starting processors
            mock_session.return_value.get.side_effect = [
                Mock(json=lambda: mock_api_responses["source_dbcp"], status_code=200),
                Mock(json=lambda: mock_api_responses["target_dbcp"], status_code=200),
                Mock(json=lambda: mock_api_responses["processors"][0], status_code=200),
                Mock(json=lambda: mock_api_responses["processors"][1], status_code=200),
                Mock(json=lambda: mock_api_responses["processors"][2], status_code=200),
                Mock(json=lambda: mock_api_responses["processors"][3], status_code=200),
                Mock(json=lambda: mock_api_responses["processors"][4], status_code=200),
            ]
            
            # Setup PUT responses
            mock_session.return_value.put.return_value = Mock(
                json=lambda: {"component": {"state": "ENABLED"}},
                status_code=200
            )
            
            # Create NiFi client
            nifi_client = NiFiAPIClient(
                test_env_setup["NIFI_API_BASE_URL"],
                test_env_setup["NIFI_API_USERNAME"],
                test_env_setup["NIFI_API_PASSWORD"]
            )
            
            # Create flow builder
            flow_builder = CDCFlowBuilder(config_parser, nifi_client)
            
            # Execute flow creation
            with patch('time.sleep'):  # Skip sleep in tests
                result = flow_builder.create_cdc_flow("test_mapping")
            
            # Verify results
            assert result["process_group"]["id"] == "cdc-pg-123"
            assert result["process_group"]["name"] == "Test CDC Mapping"
            assert result["source_dbcp"]["id"] == "source-dbcp-456"
            assert result["target_dbcp"]["id"] == "target-dbcp-789"
            assert len(result["processors"]) == 5
            
            # Verify API calls were made
            assert mock_session.return_value.post.call_count >= 9  # PG + 2 DBCP + 5 processors + connections
            assert mock_session.return_value.put.call_count >= 7   # 2 DBCP enable + 5 processor start
    
    def test_should_handle_configuration_errors_gracefully(self, test_env_setup):
        """Test error handling for missing configuration files"""
        
        config_parser = ConfigParser("/non/existent/path")
        nifi_client = NiFiAPIClient(test_env_setup["NIFI_API_BASE_URL"])
        flow_builder = CDCFlowBuilder(config_parser, nifi_client)
        
        # Should raise error for missing mapping file
        with pytest.raises(FileNotFoundError):
            flow_builder.create_cdc_flow("non_existent_mapping")
    
    def test_should_handle_nifi_api_errors(self, test_env_setup):
        """Test error handling for NiFi API failures"""
        
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_configs"
        config_parser = ConfigParser(str(fixtures_path))
        
        with patch('requests.Session') as mock_session:
            # Setup authentication
            auth_response = Mock()
            auth_response.status_code = 201
            auth_response.text = "test-jwt-token"
            
            # Setup API error response
            error_response = Mock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = Exception("Internal Server Error")
            
            mock_session.return_value.post.side_effect = [
                auth_response,  # Authentication succeeds
                error_response  # Process group creation fails
            ]
            
            nifi_client = NiFiAPIClient(
                test_env_setup["NIFI_API_BASE_URL"],
                test_env_setup["NIFI_API_USERNAME"],
                test_env_setup["NIFI_API_PASSWORD"]
            )
            
            flow_builder = CDCFlowBuilder(config_parser, nifi_client)
            
            # Should raise error when NiFi API fails
            with pytest.raises(Exception) as exc_info:
                flow_builder.create_cdc_flow("test_mapping")
            
            assert "Internal Server Error" in str(exc_info.value)
    
    @pytest.mark.integration
    def test_should_validate_created_flow_structure(self, test_env_setup, mock_api_responses):
        """Test that created flow has correct structure and relationships"""
        
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_configs"
        config_parser = ConfigParser(str(fixtures_path))
        
        # Parse the test mapping to verify expected structure
        mapping_config = config_parser.parse_mapping("test_mapping")
        
        assert mapping_config["source.datasource"] == "test_source"
        assert mapping_config["target.datasource"] == "test_target"
        assert mapping_config["source.table"] == "SCOTT.EMP_1"
        assert mapping_config["target.table"] == "SCOTT.EMP_2"
        
        # Verify datasource configurations
        source_config = config_parser.parse_datasource("test_source")
        assert source_config["db.host"] == "192.168.3.13"
        assert source_config["db.username"] == "scott"
        
        target_config = config_parser.parse_datasource("test_target")
        assert target_config["db.host"] == "192.168.3.13"
        assert target_config["db.username"] == "scott"