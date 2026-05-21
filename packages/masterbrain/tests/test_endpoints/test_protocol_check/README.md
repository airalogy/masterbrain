# Protocol Check Tests

This directory contains the complete test suite for Protocol Check functionality, modeled after the `test_vision` structure.

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all Protocol Check tests
pytest tests/test_endpoints/test_protocol_check/ -v -m protocol_check

# Run specific test files
pytest tests/test_endpoints/test_protocol_check/test_router.py -v
pytest tests/test_endpoints/test_protocol_check/test_logic.py -v
pytest tests/test_endpoints/test_protocol_check/test_protocol_check_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_protocol_check/ -v -k "qwen3.5-flash"
pytest tests/test_endpoints/test_protocol_check/ -v -k "gpt-4o-mini"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_protocol_check/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_protocol_check/test_router.py::test_protocol_check_success -v

# Use parameterized tests
pytest tests/test_endpoints/test_protocol_check/test_logic.py::test_generate_stream_success -v
```

### Method 3: Run in masterbrain conda environment

```bash
# Activate masterbrain environment first
conda activate masterbrain

# Then run tests as above
pytest tests/test_endpoints/test_protocol_check/ -v -m protocol_check
```

## Test Structure

- `conftest.py` - Test configuration and fixtures for protocol check tests
- `test_router.py` - Tests for the protocol check router endpoints  
- `test_logic.py` - Tests for protocol check logic functions
- `test_protocol_check_full_flow.py` - End-to-end tests for complete protocol check pipeline

## Test Data

The tests use sample protocol data based on the demo files:

### Protocol Types
- **AIMD Protocol**: Triangle-shaped gold nanoplate synthesis protocol
- **Python Model**: Variable model definitions with pydantic BaseModel
- **Python Assigner**: Calculator logic for protocol variables

### Sample Data Sources
- `demo_protocol_input.json` - Sample protocol check input
- `demo_model_input.json` - Sample model file input
- `demo_assigner_input.json` - Sample assigner file input

## Supported Models

The tests cover all supported models for protocol check:
- `qwen3.5-flash`
- `qwen3.5-plus`
- `gpt-4o-mini`

## Test Features

### Router Tests (`test_router.py`)
- API endpoint validation
- Request/response handling
- Parameter validation
- Error handling
- Model compatibility
- Special character handling
- Large payload testing

### Logic Tests (`test_logic.py`)
- Stream generation testing
- Target file determination logic
- Markdown code block extraction
- API error handling
- Mock client responses
- Timeout handling

### Full Flow Tests (`test_protocol_check_full_flow.py`)
- End-to-end protocol check pipeline
- Target file priority logic testing
- Model-specific behavior validation
- Performance testing
- Demo data integration
- Error recovery testing

## Test Markers

All tests are marked with `@pytest.mark.protocol_check` for easy filtering:

```bash
# Run only protocol check tests
pytest -m protocol_check

# Skip protocol check tests
pytest -m "not protocol_check"
```

## Mock Strategy

The tests use comprehensive mocking to avoid external dependencies:

- **OpenAI Client**: Mocked with `AsyncMock` to simulate LLM responses
- **Streaming Responses**: Custom async generators for testing stream handling
- **Client Selection**: Patched to return mock clients
- **API Errors**: Simulated network and service errors

## Test Coverage

The test suite covers:

- ✅ All supported models (`qwen3.5-flash`, `qwen3.5-plus`, `gpt-4o-mini`)
- ✅ All target file types (`protocol`, `model`, `assigner`)
- ✅ File priority determination logic
- ✅ Streaming response handling
- ✅ Markdown code block extraction
- ✅ Error handling and recovery
- ✅ Parameter validation
- ✅ Performance and timeout behavior
- ✅ Special character and Unicode support
- ✅ Large payload handling

## Integration with Demo Data

The tests are designed to work with the existing demo files in the directory:
- Uses the same data structures as demo inputs
- Validates against expected output patterns
- Ensures compatibility with real usage scenarios

## Debugging

To debug test failures:

```bash
# Run with verbose output and no capture
pytest tests/test_endpoints/test_protocol_check/ -v -s

# Run single test with debug output
DEBUG=true pytest tests/test_endpoints/test_protocol_check/test_router.py::test_protocol_check_success -v -s

# Add breakpoints in test code using:
import pdb; pdb.set_trace()
```

## Notes

- Tests may require proper environment setup to access the protocol check logic
- Some tests use timeouts to prevent hanging on slow operations
- Mock responses are designed to simulate realistic protocol check outputs
- All tests maintain compatibility with the existing masterbrain testing framework
