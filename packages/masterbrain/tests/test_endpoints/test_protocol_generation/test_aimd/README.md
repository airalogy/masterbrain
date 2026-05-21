# AIMD (Protocol Generation) Tests

This directory contains the complete test suite for AIMD functionality, modeled after the `test_vision` structure.

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all AIMD tests
pytest tests/test_endpoints/test_protocol_generation/test_aimd/ -v -m aimd

# Run specific test files
pytest tests/test_endpoints/test_protocol_generation/test_aimd/test_router.py -v
pytest tests/test_endpoints/test_protocol_generation/test_aimd/test_logic.py -v
pytest tests/test_endpoints/test_protocol_generation/test_aimd/test_aimd_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_protocol_generation/test_aimd/ -v -k "qwen3.5-flash"
pytest tests/test_endpoints/test_protocol_generation/test_aimd/ -v -k "qwen3.5-plus"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_protocol_generation/test_aimd/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_protocol_generation/test_aimd/test_router.py::test_aimd_protocol_generation_success -v

# Use parameterized tests
pytest tests/test_endpoints/test_protocol_generation/test_aimd/test_logic.py::test_generate_stream_success -v
```

### Method 3: Run in masterbrain conda environment

```bash
# Activate masterbrain environment first
conda activate masterbrain

# Then run tests as above
pytest tests/test_endpoints/test_protocol_generation/test_aimd/ -v -m aimd
```

## Test Structure

- `conftest.py` - Test configuration and fixtures for AIMD tests
- `test_router.py` - Tests for the AIMD router endpoints
- `test_logic.py` - Tests for protocol generation logic functions
- `test_aimd_full_flow.py` - End-to-end tests for complete protocol generation pipeline

## Test Data

The tests use the following demo data:
- `demo_input.json` - Sample input data for protocol generation requests
- `demo_output.txt` - Expected output format for protocol generation

## Test Features

### Router Tests (`test_router.py`)
- Protocol generation endpoint testing
- Model configuration validation  
- Input validation (missing/empty instructions)
- Error handling for invalid models
- Support for different model configurations (thinking, search)

### Logic Tests (`test_logic.py`)
- Stream generation functionality
- Async protocol generation testing
- Mocked client responses
- Error handling and timeout scenarios
- Model parameter validation

### Full Flow Tests (`test_aimd_full_flow.py`)
- Complete protocol generation pipeline
- Integration with demo data
- System prompt integration
- Thinking mode testing
- Long instruction handling
- Multi-language support (Chinese/English)

## Special Test Considerations

### Streaming Response
AIMD uses streaming responses, so tests need to handle:
- Async iteration over chunks
- Proper chunk collection and assembly
- Timeout handling for slow responses

### Model Support
Tests are parameterized across supported models:
- `qwen3.5-flash`
- `qwen3.5-plus`
- `gpt-4o-mini`

### Mocking Strategy
Due to the nature of LLM APIs, tests extensively use mocking:
- Mock OpenAI client responses
- Mock streaming chunk generation
- Mock error conditions for robustness testing

### Demo Data Integration
Tests use real demo data from:
- `demo_input.json` - Real input format
- `demo_output.txt` - Expected AIMD format output

This ensures tests validate against realistic protocol generation scenarios.

## Expected Test Outcomes

In CI/CD environments without proper API credentials:
- Tests may return status codes 400/500 instead of 200
- This is expected behavior and tests accommodate this
- Focus is on validating request/response structure and error handling

For local development with proper API setup:
- Tests should return 200 status codes
- Generated content should match expected AIMD format patterns
- Protocol structure should include variables, steps, and checks
