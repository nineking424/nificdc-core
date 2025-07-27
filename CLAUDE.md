# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a NiFi-based CDC (Change Data Capture) core implementation project. The initial focus is on Oracle-to-Oracle database CDC, with plans to expand to multiple databases (PostgreSQL, etc.) and data sources (local, FTP, S3, Kafka, RabbitMQ, Redis, etc.).

**Important**: This project uses Apache NiFi 1.28 deployed externally. We leverage the NiFi API to programmatically create and manage processors rather than deploying custom NAR files.

## Development Setup

### Prerequisites
- Apache NiFi 1.28 (deployed externally)
- Java 8+ (for NiFi 1.28 compatibility)
- Access to NiFi REST API endpoints
- Technology stack to be determined during implementation

### Environment Setup
1. Copy `.env.example` to `.env`
2. Fill in the required connection information
3. Ensure NiFi API is accessible from your development environment

### Common Commands

#### Build Commands
```bash
# Build commands will be determined based on chosen technology stack
# Examples:
# Java/Maven: mvn clean install
# Python: pip install -r requirements.txt
# Node.js: npm install
```

#### NiFi API Interaction
```bash
# Get NiFi cluster status
curl -X GET http://nifi-host:8080/nifi-api/flow/cluster/summary

# List all process groups
curl -X GET http://nifi-host:8080/nifi-api/process-groups/root/process-groups

# Create a new processor
curl -X POST http://nifi-host:8080/nifi-api/process-groups/{id}/processors \
  -H 'Content-Type: application/json' \
  -d '{"revision":{"version":0},"component":{"type":"org.apache.nifi.processors.standard.GetFile","name":"GetFile"}}'
```

## Architecture Guidelines

### Core Components Structure

Since we're using NiFi API instead of custom processors, the architecture will focus on:

1. **API Client Module**
   - NiFi REST API client implementation
   - Authentication and session management
   - Process group and processor management
   - Flow configuration and monitoring

2. **CDC Configuration Module**
   - Database connection configurations
   - CDC strategy configurations per database type
   - Processor template definitions
   - Flow design patterns for CDC

3. **Flow Management Module**
   - Automated flow creation for CDC pipelines
   - Process group templates for different CDC scenarios
   - Connection and relationship management
   - Error handling and retry configurations

4. **Monitoring Module**
   - Flow performance monitoring via NiFi API
   - CDC lag monitoring
   - Error tracking and alerting
   - Health check implementations

### Key Design Patterns

1. **NiFi API Integration Pattern**
   - Use REST API for all NiFi interactions
   - Implement proper authentication (certificates/tokens)
   - Handle API versioning for NiFi 1.28
   - Implement retry logic for API calls

2. **CDC Flow Templates**
   - Create reusable process group templates
   - Use NiFi's built-in processors where possible:
     - ExecuteSQL/QueryDatabaseTable for polling
     - ConsumeKafka/PublishKafka for streaming
     - PutDatabaseRecord for target updates
   - Implement custom logic via ExecuteScript processors when needed

3. **CDC Implementation Strategy**
   - For Oracle: Configure CaptureChangeMySQL or ExecuteSQL with CDC queries
   - For PostgreSQL: Use logical replication with ConsumeKafka
   - Leverage NiFi's Record processors for data transformation

### Configuration Management

- Configure NiFi Controller Services via API for connection pooling
- Use NiFi Variables and Parameter Contexts for environment-specific configs
- Store sensitive credentials in NiFi's Parameter Contexts with sensitivity flag
- Implement configuration versioning and backup

### Error Handling

- Configure processor retry settings via API
- Set up failure routing in processor relationships
- Implement dead letter queues using RouteOnAttribute
- Monitor bulletin board for processor errors via API

### Performance Considerations

- Configure concurrent tasks for processors via API
- Set appropriate back pressure thresholds
- Use NiFi clustering features for scalability
- Monitor queue sizes and processing rates via API

## Testing Guidelines

### Test-Driven Development (TDD) Approach

**IMPORTANT**: This project follows Test-Driven Development principles. Always write tests before implementing features.

#### TDD Workflow
1. **Red**: Write a failing test that defines the desired functionality
2. **Green**: Write the minimum code necessary to make the test pass
3. **Refactor**: Improve the code while keeping tests green

#### Test Structure
```
tests/
├── unit/
│   ├── test_nifi_api_client.py
│   ├── test_config_parser.py
│   └── test_cdc_flow_builder.py
├── integration/
│   ├── test_nifi_integration.py
│   └── test_database_connectivity.py
└── fixtures/
    ├── sample_configs/
    └── mock_responses/
```

#### Testing Best Practices
1. **Unit Tests**
   - Mock all external dependencies (NiFi API, databases)
   - Test edge cases and error scenarios
   - Aim for >80% code coverage
   - Use descriptive test names: `test_should_create_processor_when_valid_config()`

2. **Integration Tests**
   - Use test NiFi instance with known state
   - Test actual API calls with timeout handling
   - Verify end-to-end CDC flow creation
   - Clean up test artifacts after each run

3. **Test Examples**
```python
# Example: Testing NiFi API client
def test_should_create_process_group_with_valid_params():
    # Arrange
    client = NiFiAPIClient("http://test-nifi:8080/nifi-api")
    expected_name = "Test CDC Group"
    
    # Act
    result = client.create_process_group("root", expected_name)
    
    # Assert
    assert result["component"]["name"] == expected_name
    assert "id" in result["component"]

# Example: Testing error handling
def test_should_raise_exception_when_nifi_unavailable():
    # Arrange
    client = NiFiAPIClient("http://invalid-host/nifi-api")
    
    # Act & Assert
    with pytest.raises(ConnectionError):
        client.create_process_group("root", "Test")
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_nifi_api_client.py

# Run tests in watch mode (TDD)
pytest-watch
```

#### Mock Strategy
- Use `unittest.mock` for Python implementations
- Create fixture files for NiFi API responses
- Mock database connections with in-memory alternatives
- Use dependency injection for testability

### Legacy Testing Guidelines

1. Test NiFi API client with mock responses
2. Create test flows in development NiFi instance
3. Implement flow validation before deployment
4. Load testing with production-like data volumes

## Future Expansion Notes

When adding new data sources:
1. Design new process group template for the data source
2. Identify required NiFi processors (built-in or ExecuteScript)
3. Create API client methods for flow deployment
4. Add source-specific configuration templates
5. Implement monitoring for the new source type
6. Document the flow design and configuration

## NiFi API Resources

### Key API Endpoints for NiFi 1.28
- `/nifi-api/flow` - Flow information
- `/nifi-api/process-groups` - Process group management
- `/nifi-api/processors` - Processor operations
- `/nifi-api/controller-services` - Controller service management
- `/nifi-api/parameter-contexts` - Parameter context operations
- `/nifi-api/flow/bulletin-board` - Error and status bulletins

### Technology Stack Considerations

As the technology stack is determined during implementation, consider:
- **Java**: Natural fit for NiFi integration, good API client libraries
- **Python**: Good for rapid prototyping, requests library for REST API
- **Node.js**: Async nature suits API interactions, good for real-time monitoring
- **Go**: High performance, good for concurrent API operations

## Git Workflow

Always create meaningful commits that reflect the CDC implementation progress:
```bash
git add .
git commit -m "feat: Add Oracle CDC flow template via NiFi API"
```