import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config_parser import ConfigParser


class TestConfigParser:
    
    @pytest.fixture
    def config_parser(self):
        """Create ConfigParser instance with test fixtures path"""
        test_base_path = Path(__file__).parent.parent / "fixtures" / "sample_configs"
        return ConfigParser(str(test_base_path))
    
    def test_should_parse_datasource_properties_file(self, config_parser):
        # Act
        result = config_parser.parse_datasource("test_source")
        
        # Assert
        assert result["db.type"] == "oracle"
        assert result["db.host"] == "192.168.3.13"
        assert result["db.port"] == "1521"
        assert result["db.service.name"] == "ORCL"
        assert result["db.username"] == "scott"
        assert result["db.password"] == "tiger"
        assert result["db.pool.size"] == "10"
    
    def test_should_parse_mapping_properties_file(self, config_parser):
        # Act
        result = config_parser.parse_mapping("test_mapping")
        
        # Assert
        assert result["mapping.name"] == "Test Oracle to Oracle CDC"
        assert result["source.datasource"] == "test_source"
        assert result["target.datasource"] == "test_target"
        assert result["cdc.mode"] == "incremental"
        assert result["cdc.polling.interval"] == "5000"
        assert result["source.table"] == "SCOTT.EMP_1"
        assert result["target.table"] == "SCOTT.EMP_2"
    
    def test_should_get_environment_configuration(self, config_parser):
        # Arrange - Set environment variables for test
        with patch.dict(os.environ, {
            "NIFI_API_BASE_URL": "http://test-nifi:8080/nifi-api",
            "NIFI_API_USERNAME": "test_user",
            "NIFI_API_PASSWORD": "test_pass"
        }):
            # Act
            result = config_parser.get_env_config()
            
            # Assert
            assert result["nifi_api_base_url"] == "http://test-nifi:8080/nifi-api"
            assert result["nifi_api_username"] == "test_user"
            assert result["nifi_api_password"] == "test_pass"
            assert result["nifi_root_process_group_id"] == "root"
            assert result["nifi_cdc_process_group_name"] == "CDC-Flows"
    
    def test_should_build_oracle_jdbc_url(self, config_parser):
        # Arrange
        db_properties = {
            "db.type": "oracle",
            "db.host": "localhost",
            "db.port": "1521",
            "db.service.name": "ORCL"
        }
        
        # Act
        result = config_parser.build_jdbc_url(db_properties)
        
        # Assert
        assert result == "jdbc:oracle:thin:@localhost:1521:ORCL"
    
    def test_should_return_empty_string_for_unsupported_database(self, config_parser):
        # Arrange
        db_properties = {
            "db.type": "postgresql"
        }
        
        # Act
        result = config_parser.build_jdbc_url(db_properties)
        
        # Assert
        assert result == ""
    
    def test_should_raise_error_when_datasource_file_not_found(self, config_parser):
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config_parser.parse_datasource("non_existent")
    
    def test_should_raise_error_when_mapping_file_not_found(self, config_parser):
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config_parser.parse_mapping("non_existent")
    
    def test_should_handle_properties_file_format(self):
        # Arrange
        properties_content = """
# Database settings
db.host=localhost
db.port=1521

# Pool settings  
db.pool.size=10
"""
        test_base_path = "/test/path"
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=properties_content)):
                parser = ConfigParser(test_base_path)
                
                # Act
                result = parser.parse_datasource("test")
        
        # Assert
        assert result["db.host"] == "localhost"
        assert result["db.port"] == "1521"
        assert result["db.pool.size"] == "10"
    
    def test_should_handle_empty_properties_file(self):
        # Arrange
        test_base_path = "/test/path"
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="")):
                parser = ConfigParser(test_base_path)
                
                # Act
                result = parser.parse_mapping("empty")
        
        # Assert
        assert result == {}
    
    def test_should_ignore_comments_and_empty_lines(self):
        # Arrange
        properties_content = """
# This is a comment
key1=value1

# Another comment
key2=value2

"""
        test_base_path = "/test/path"
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=properties_content)):
                parser = ConfigParser(test_base_path)
                
                # Act
                result = parser.parse_mapping("test")
        
        # Assert
        assert result == {"key1": "value1", "key2": "value2"}
        assert len(result) == 2