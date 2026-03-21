# Model (Protocol Generation) Tests

This directory contains the complete test suite for Model functionality, modeled after the `test_aimd` structure.

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all Model tests
pytest tests/test_endpoints/test_protocol_generation/test_model/ -v -m model

# Run specific test files
pytest tests/test_endpoints/test_protocol_generation/test_model/test_router.py -v
pytest tests/test_endpoints/test_protocol_generation/test_model/test_logic.py -v
pytest tests/test_endpoints/test_protocol_generation/test_model/test_model_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_protocol_generation/test_model/ -v -k "qwen3.5-flash"
pytest tests/test_endpoints/test_protocol_generation/test_model/ -v -k "qwen3.5-plus"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_protocol_generation/test_model/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_protocol_generation/test_model/test_router.py::test_model_protocol_generation_success -v

# Use parameterized tests
pytest tests/test_endpoints/test_protocol_generation/test_model/test_logic.py::test_generate_stream_success -v
```

### Method 3: Run in masterbrain conda environment

```bash
# Activate masterbrain environment first
conda activate masterbrain

# Then run tests as above
pytest tests/test_endpoints/test_protocol_generation/test_model/ -v -m model
```

## Test Structure

- `conftest.py` - Test configuration and fixtures for Model tests
- `test_router.py` - Tests for the Model router endpoints
- `test_logic.py` - Tests for model.py generation logic functions
- `test_model_full_flow.py` - End-to-end tests for complete model.py generation pipeline

## Test Data

The tests use the following demo data:
- `demo_input.json` - Sample input data including protocol_aimd for model generation requests
- `demo_output.txt` - Expected model.py output format

## Test Features

### Router Tests (`test_router.py`)
- Model generation endpoint testing (`/protocol_generation/model`)
- Model configuration validation  
- Input validation (missing/empty protocol_aimd)
- Error handling for invalid models
- Support for different model configurations (thinking, search)
- Complex protocol_aimd handling

### Logic Tests (`test_logic.py`)
- Stream generation functionality for model.py code
- Async model generation testing
- Mocked client responses
- Error handling and timeout scenarios
- Model parameter validation
- Protocol_aimd to model.py transformation

### Full Flow Tests (`test_model_full_flow.py`)
- Complete model.py generation pipeline
- Integration with demo data
- System prompt integration
- Thinking mode testing
- Long protocol_aimd handling
- Multi-language support (Chinese/English)
- Complex AIMD structure processing

## Special Test Considerations

### Streaming Response
Model generation uses streaming responses, so tests need to handle:
- Async iteration over chunks
- Proper chunk collection and assembly
- Timeout handling for slow responses

### Input Format
Model tests specifically handle:
- `protocol_aimd` input field (from AIMD stage)
- Conversion from AIMD format to Python model code
- Variable extraction and type mapping

### Output Validation
Tests verify model.py output contains:
- Proper Pydantic BaseModel structure
- Correct field definitions with types
- Import statements for required modules
- Field descriptions and default values

### Model Support
Tests are parameterized across supported models:
- `qwen3.5-flash`
- `qwen3.5-plus`

### Mocking Strategy
Due to the nature of LLM APIs, tests extensively use mocking:
- Mock OpenAI client responses
- Mock streaming chunk generation for Python code
- Mock error conditions for robustness testing
- Simulate model.py code generation patterns

### Demo Data Integration
Tests use real demo data from:
- `demo_input.json` - Real input format with protocol_aimd content
- `demo_output.txt` - Expected model.py format output with Pydantic models

This ensures tests validate against realistic model.py generation scenarios.

## Expected Test Outcomes

In CI/CD environments without proper API credentials:
- Tests may return status codes 400/500 instead of 200
- This is expected behavior and tests accommodate this
- Focus is on validating request/response structure and error handling

For local development with proper API setup:
- Tests should return 200 status codes
- Generated content should match expected model.py format patterns
- Model structure should include BaseModel classes, Field definitions, and proper imports

## Key Differences from AIMD Tests

1. **Input Format**: Uses `protocol_aimd` field instead of `instruction`
2. **Output Format**: Generates Python model.py code instead of AIMD protocol format
3. **Validation Logic**: Checks for Python class definitions, imports, and Pydantic structures
4. **Stage Position**: This is Stage 2 in the protocol generation pipeline (after AIMD)

## Pipeline Integration

The Model tests are part of the three-stage protocol generation pipeline:
1. AIMD Stage: `instruction` → `protocol.aimd`
2. **Model Stage**: `protocol_aimd` → `model.py` (THIS STAGE)
3. Assigner Stage: `protocol_aimd` + `model.py` → `assigner.py`
