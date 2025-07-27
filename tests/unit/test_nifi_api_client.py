import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import requests

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nifi_api_client import NiFiAPIClient


class TestNiFiAPIClient:
    
    @pytest.fixture
    def mock_responses(self):
        """Load mock responses from fixture file"""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "mock_responses" / "nifi_api_responses.json"
        with open(fixture_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def client(self):
        """Create NiFi API client without authentication"""
        return NiFiAPIClient("http://test-nifi:8080/nifi-api")
    
    @pytest.fixture
    def authenticated_client(self):
        """Create NiFi API client with authentication"""
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.text = "test-jwt-token"
            client = NiFiAPIClient("http://test-nifi:8080/nifi-api", "test_user", "test_pass")
            return client
    
    def test_should_initialize_client_without_authentication(self):
        # Act
        client = NiFiAPIClient("http://test-nifi:8080/nifi-api")
        
        # Assert
        assert client.base_url == "http://test-nifi:8080/nifi-api"
        assert client.username is None
        assert client.password is None
    
    def test_should_initialize_client_with_authentication(self):
        # Arrange
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.text = "test-jwt-token"
            
            # Act
            client = NiFiAPIClient("http://test-nifi:8080/nifi-api", "test_user", "test_pass")
            
            # Assert
            assert client.username == "test_user"
            assert client.password == "test_pass"
            mock_post.assert_called_once()
            assert client.session.headers['Authorization'] == 'Bearer test-jwt-token'
    
    def test_should_strip_trailing_slash_from_base_url(self):
        # Act
        client = NiFiAPIClient("http://test-nifi:8080/nifi-api/")
        
        # Assert
        assert client.base_url == "http://test-nifi:8080/nifi-api"
    
    def test_should_create_process_group(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_responses["process_group_response"]
            mock_post.return_value.status_code = 201
            
            # Act
            result = client.create_process_group("root", "Test Process Group")
            
            # Assert
            assert result["component"]["id"] == "test-pg-123"
            assert result["component"]["name"] == "Test Process Group"
            mock_post.assert_called_once()
            
            # Verify the request
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://test-nifi:8080/nifi-api/process-groups/root/process-groups"
            assert call_args[1]["json"]["component"]["name"] == "Test Process Group"
    
    def test_should_create_processor(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_responses["processor_response"]
            mock_post.return_value.status_code = 201
            
            properties = {"SQL select query": "SELECT * FROM TEST"}
            
            # Act
            result = client.create_processor(
                "test-pg-123",
                "org.apache.nifi.processors.standard.ExecuteSQL",
                "Test Processor",
                properties
            )
            
            # Assert
            assert result["component"]["id"] == "test-proc-456"
            assert result["component"]["type"] == "org.apache.nifi.processors.standard.ExecuteSQL"
            mock_post.assert_called_once()
    
    def test_should_create_processor_with_custom_position(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_responses["processor_response"]
            mock_post.return_value.status_code = 201
            
            # Act
            result = client.create_processor(
                "test-pg-123",
                "org.apache.nifi.processors.standard.ExecuteSQL",
                "Test Processor",
                {},
                {"x": 100, "y": 200}
            )
            
            # Assert
            call_args = mock_post.call_args
            assert call_args[1]["json"]["component"]["position"] == {"x": 100, "y": 200}
    
    def test_should_create_controller_service(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_responses["controller_service_response"]
            mock_post.return_value.status_code = 201
            
            properties = {
                "Database Connection URL": "jdbc:oracle:thin:@localhost:1521:ORCL",
                "Database User": "test_user"
            }
            
            # Act
            result = client.create_controller_service(
                "test-pg-123",
                "org.apache.nifi.dbcp.DBCPConnectionPool",
                "Test DBCP",
                properties
            )
            
            # Assert
            assert result["component"]["id"] == "test-dbcp-789"
            assert result["component"]["type"] == "org.apache.nifi.dbcp.DBCPConnectionPool"
    
    def test_should_enable_controller_service(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'get') as mock_get:
            with patch.object(client.session, 'put') as mock_put:
                mock_get.return_value.json.return_value = mock_responses["controller_service_response"]
                mock_get.return_value.status_code = 200
                
                enabled_response = mock_responses["controller_service_response"].copy()
                enabled_response["component"]["state"] = "ENABLED"
                mock_put.return_value.json.return_value = enabled_response
                mock_put.return_value.status_code = 200
                
                # Act
                result = client.enable_controller_service("test-dbcp-789")
                
                # Assert
                assert result["component"]["state"] == "ENABLED"
                mock_get.assert_called_once()
                mock_put.assert_called_once()
    
    def test_should_create_connection(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_responses["connection_response"]
            mock_post.return_value.status_code = 201
            
            # Act
            result = client.create_connection(
                "test-pg-123",
                "test-proc-456",
                "test-proc-457",
                ["success"]
            )
            
            # Assert
            assert result["component"]["id"] == "test-conn-111"
            assert result["component"]["selectedRelationships"] == ["success"]
    
    def test_should_start_processor(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'get') as mock_get:
            with patch.object(client.session, 'put') as mock_put:
                mock_get.return_value.json.return_value = mock_responses["processor_response"]
                mock_get.return_value.status_code = 200
                
                running_response = mock_responses["processor_response"].copy()
                running_response["component"]["state"] = "RUNNING"
                mock_put.return_value.json.return_value = running_response
                mock_put.return_value.status_code = 200
                
                # Act
                result = client.start_processor("test-proc-456")
                
                # Assert
                assert result["component"]["state"] == "RUNNING"
    
    def test_should_get_process_group(self, client, mock_responses):
        # Arrange
        with patch.object(client.session, 'get') as mock_get:
            mock_get.return_value.json.return_value = mock_responses["process_group_response"]
            mock_get.return_value.status_code = 200
            
            # Act
            result = client.get_process_group("test-pg-123")
            
            # Assert
            assert result["component"]["id"] == "test-pg-123"
            assert result["component"]["name"] == "Test Process Group"
    
    def test_should_raise_exception_on_api_error(self, client):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            
            # Act & Assert
            with pytest.raises(requests.HTTPError):
                client.create_process_group("invalid", "Test")
    
    def test_should_raise_exception_on_connection_error(self, client):
        # Arrange
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Connection refused")
            
            # Act & Assert
            with pytest.raises(requests.ConnectionError):
                client.create_process_group("root", "Test")
    
    def test_should_handle_authentication_failure(self):
        # Arrange
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 401
            
            # Act
            client = NiFiAPIClient("http://test-nifi:8080/nifi-api", "invalid_user", "invalid_pass")
            
            # Assert
            assert 'Authorization' not in client.session.headers
    
    def test_should_generate_unique_client_id(self, client):
        # Act
        client_id1 = client._get_client_id()
        import time
        time.sleep(1)  # Use 1 second delay to ensure different timestamp
        client_id2 = client._get_client_id()
        
        # Assert
        assert client_id1.startswith("nifi-cdc-client-")
        assert client_id2.startswith("nifi-cdc-client-")
        assert client_id1 != client_id2