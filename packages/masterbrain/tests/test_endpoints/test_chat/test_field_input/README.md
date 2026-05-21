# Field Input Tests

This directory contains the complete test suite for Field Input functionality, which provides automatic slot filling for experimental data based on protocol schemas.

## Overview

The Field Input endpoint automatically extracts relevant information from user input (text or images) and fills predefined slots/fields based on the provided protocol schema. This is particularly useful for experimental data recording and protocol compliance.

## Test Structure

### Core Test Files

- **`conftest.py`** - Test configuration, fixtures, and common test data
- **`test_router.py`** - FastAPI router endpoint tests
- **`test_slot_service.py`** - Core business logic tests for slot extraction
- **`test_types.py`** - Data model validation and serialization tests
- **`test_field_input_full_flow.py`** - End-to-end workflow tests

### Test Data Files

- **`text_in_*.json`** - Text input test cases
- **`text_out_*.json`** - Expected text output responses
- **`imgL_in_*.json`** - Image URL input test cases
- **`imgL_out_*.json`** - Expected image URL output responses
- **`imgP_in_*.json`** - Base64 image input test cases
- **`imgP_out_*.json`** - Expected base64 image output responses

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all Field Input tests
pytest tests/test_endpoints/test_chat/test_field_input/ -v -m field_input

# Run specific test files
pytest tests/test_endpoints/test_chat/test_field_input/test_router.py -v
pytest tests/test_endpoints/test_chat/test_field_input/test_slot_service.py -v
pytest tests/test_endpoints/test_chat/test_field_input/test_types.py -v
pytest tests/test_endpoints/test_chat/test_field_input/test_field_input_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_chat/test_field_input/ -v -k "gpt-4o-mini"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_chat/test_field_input/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_chat/test_field_input/test_router.py::test_field_input_successful_request -v

# Use parameterized tests
pytest tests/test_endpoints/test_chat/test_field_input/test_router.py::test_field_input_successful_request -v -k "gpt-4o-mini"
```

## Test Categories

### 1. Router Tests (`test_router.py`)

Tests the FastAPI endpoint functionality:
- Endpoint accessibility and routing
- Request validation (missing fields, invalid data)
- Response structure validation
- Error handling for malformed requests

### 2. Slot Service Tests (`test_slot_service.py`)

Tests the core business logic:
- Schema loading and parsing
- Required field extraction
- Update information formatting
- Image detection (URLs and base64)
- Slot memory management

### 3. Type Tests (`test_types.py`)

Tests data model validation:
- Pydantic model validation
- Required field enforcement
- Serialization/deserialization
- Complex nested data structures

### 4. Full Flow Tests (`test_field_input_full_flow.py`)

Tests complete workflows:
- End-to-end text input processing
- Image input processing
- Multiple conversation history handling
- Error scenarios
- Metadata preservation

## Key Features Tested

### Slot Extraction
- Automatic field identification from user input
- Protocol schema compliance
- Multi-format input support (text, images)

### Image Processing
- URL-based image recognition
- Base64 encoded image handling
- Automatic text extraction from images

### Protocol Schema Support
- JSON Schema validation
- Required field enforcement
- Nested object definitions
- Reference resolution

### Tool Call Generation
- Automatic slot filling operation creation
- Structured response formatting
- Unique ID generation for operations

## Test Scenarios

### Text Input Scenarios
- Simple field value extraction
- Multiple field updates in single message
- Chinese text processing
- Scientific notation handling

### Image Input Scenarios
- Image URL processing
- Base64 image decoding
- OCR result cleaning
- Multi-image message handling

### Error Scenarios
- Invalid protocol schemas
- Missing required fields
- Malformed input data
- API service failures

### Edge Cases
- Empty schemas
- No field updates needed
- Large conversation histories
- Complex nested data structures

## Configuration

### Test Fixtures

The `conftest.py` file provides:
- `field_input_test_config` - Global test configuration
- `sample_protocol_schema` - Standard test schema
- `mock_field_input_request` - Request factory function
- `sample_image_url` - Test image URL
- `sample_base64_image` - Test base64 image data

### Environment Variables

- `DEBUG` - Enable debug output during tests
- `PYTEST_TIMEOUT` - Test timeout configuration

## Mocking Strategy

Tests use extensive mocking to:
- Isolate unit test components
- Avoid external API calls
- Control test data and responses
- Simulate error conditions

Key mocked components:
- `SlotMemory` class for slot extraction logic
- `create_slot_extraction_prompt` for prompt generation
- External LLM API clients

## Performance Considerations

- Tests are designed to run quickly without external dependencies
- Mocked responses simulate realistic API behavior
- Parameterized tests cover multiple model configurations
- Async tests handle concurrent operations properly

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the test environment has access to the `masterbrain` package
2. **Mock Failures**: Check that mock patches target the correct import paths
3. **Validation Errors**: Verify test data matches expected schema requirements
4. **Async Test Failures**: Ensure proper `@pytest.mark.asyncio` decorators

### Debug Mode

Enable debug output to see detailed test execution:

```bash
DEBUG=true pytest tests/test_endpoints/test_chat/test_field_input/ -v -s
```

This will show:
- Mock setup and teardown
- Request/response data
- Slot extraction details
- Tool call generation steps
