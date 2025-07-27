# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a NiFi-based CDC (Change Data Capture) core implementation project. The initial focus is on Oracle-to-Oracle database CDC, with plans to expand to multiple databases (PostgreSQL, etc.) and data sources (local, FTP, S3, Kafka, RabbitMQ, Redis, etc.).

## Development Setup

### Prerequisites
- Apache NiFi (1.x or 2.x)
- Java 8+ (for NiFi compatibility)
- Oracle JDBC drivers
- Maven or Gradle for dependency management

### Common Commands

#### Build Commands
```bash
# Maven build
mvn clean install
mvn package

# Gradle build (if using Gradle)
./gradlew clean build
```

#### Testing
```bash
# Run unit tests
mvn test
./gradlew test

# Run integration tests
mvn verify
./gradlew integrationTest
```

#### NiFi Processor Development
```bash
# Deploy custom processor to NiFi
cp target/*.nar $NIFI_HOME/lib/
# Restart NiFi to load new processors
```

## Architecture Guidelines

### Core Components Structure

1. **Processors Package** (`com.nificdc.processors`)
   - Custom NiFi processors for CDC operations
   - Each database type should have its own processor class
   - Follow NiFi processor lifecycle methods

2. **Services Package** (`com.nificdc.services`)
   - Database connection management
   - CDC logic implementation
   - Transaction log readers

3. **Models Package** (`com.nificdc.models`)
   - Data transfer objects
   - CDC event models
   - Configuration models

4. **Utils Package** (`com.nificdc.utils`)
   - Common utilities
   - Database-specific helpers
   - Data transformation utilities

### Key Design Patterns

1. **NiFi Processor Pattern**
   - Extend `AbstractProcessor`
   - Implement `onTrigger()` for main logic
   - Use PropertyDescriptors for configuration
   - Handle FlowFile processing properly

2. **Database Abstraction**
   - Create interfaces for database operations
   - Implement database-specific classes
   - Use factory pattern for database connections

3. **CDC Implementation Strategy**
   - For Oracle: Use LogMiner or GoldenGate APIs
   - For PostgreSQL: Use logical replication
   - Implement polling or streaming based on source

### Configuration Management

- Use NiFi's Controller Services for connection pooling
- Store sensitive credentials in NiFi's sensitive properties
- Use PropertyDescriptors for processor configuration

### Error Handling

- Implement proper rollback mechanisms
- Route failed FlowFiles to failure relationships
- Log detailed error information for debugging
- Implement retry logic with exponential backoff

### Performance Considerations

- Batch processing for better throughput
- Connection pooling for database connections
- Implement checkpoint mechanisms for recovery
- Monitor memory usage in processors

## Testing Guidelines

1. Unit test all processors with MockProcessContext
2. Integration tests with embedded databases when possible
3. Test error scenarios and edge cases
4. Performance testing with large data volumes

## Future Expansion Notes

When adding new data sources:
1. Create new processor in appropriate package
2. Implement source-specific reader/writer
3. Add configuration properties
4. Update documentation
5. Add comprehensive tests

## Git Workflow

Always create meaningful commits that reflect the CDC implementation progress:
```bash
git add .
git commit -m "feat: Add Oracle CDC processor with LogMiner support"
```