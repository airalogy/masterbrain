# Assigner Protocol Generation Tests

This directory contains test code for testing the Assigner protocol generation functionality. Assigner is the third step in the protocol generation pipeline, responsible for generating executable assigner.py files based on protocol.aimd and protocol.model content.

## File Structure

- `conftest.py` - Test configuration and fixtures
- `test_logic.py` - Core logic tests (generate_stream function)
- `test_router.py` - FastAPI router tests
- `test_assigner_full_flow.py` - End-to-end flow tests
- `demo_input.json` - Demo input data
- `demo_output.txt` - Expected output example
- `__init__.py` - Package identifier file
- `README.md` - Documentation (this file)

## Test Coverage

### 1. Logic Tests (`test_logic.py`)

Tests the `generate_stream` function in various scenarios:

- **Basic functionality tests**: Using different models (qwen3.5-flash, qwen3.5-plus, gpt-4o-mini)
- **Code block filtering tests**: Verifying correct handling of `\`\`\`python` and `\`\`\`` markers
- **No-marker fallback tests**: Degraded handling when no code markers are present
- **Error handling tests**: Handling API errors, timeouts, empty responses
- **Thinking mode tests**: Handling enable_thinking=True
- **Demo data tests**: Testing with demo_input.json data
- **History modification tests**: Verifying correct conversation history updates

### 2. Router Tests (`test_router.py`)

Tests FastAPI router in various scenarios:

- **Successful request tests**: Normal requests with different models
- **Missing field tests**: Handling missing protocol_aimd, protocol_model
- **Invalid model tests**: Validation of invalid model names
- **Various configuration tests**: Enabling thinking mode, search mode
- **Multi-language protocol tests**: Chinese, English protocol content
- **Complex protocol tests**: Large, complex protocol content
- **Format error tests**: Handling malformed JSON

### 3. Full Flow Tests (`test_assigner_full_flow.py`)

End-to-end testing of the complete Assigner flow:

- **Complete flow tests**: Full flow from input to assigner.py generation
- **Demo data flow tests**: Complete flow using demo data
- **Thinking mode flow tests**: Complete flow with thinking mode enabled
- **Error recovery tests**: Handling various error situations
- **Complex protocol flow tests**: End-to-end handling of complex protocols
- **Multi-language flow tests**: Handling different language protocols
- **Timeout handling tests**: Network timeout and other exceptional situations
- **System prompt integration tests**: Correct integration of system prompts

## Key Features

### Code Block Filtering
A key feature of Assigner is extracting pure Python code from LLM responses:
- Detecting `\`\`\`python\n` start marker
- Detecting `\`\`\`` end marker
- Filtering out content outside markers
- Fallback mechanism for no-marker situations

### Input Requirements
Assigner requires two core inputs:
- `protocol_aimd`: Standardized experimental protocol format
- `protocol_model`: Pydantic model definition

### Output Format
Generated assigner.py files contain:
- `AssignerBase` class inheritance
- `@assigner` decorator configuration
- Static method implementing calculation logic
- `AssignerResult` return results

## Running Tests

### Run All Assigner Tests

```bash
# Run in masterbrain conda environment
conda activate masterbrain
pytest tests/test_endpoints/test_protocol_generation/test_assigner/ -v
```

### Run Specific Test Files

```bash
# Logic tests
pytest tests/test_endpoints/test_protocol_generation/test_assigner/test_logic.py -v

# Router tests
pytest tests/test_endpoints/test_protocol_generation/test_assigner/test_router.py -v

# Full flow tests
pytest tests/test_endpoints/test_protocol_generation/test_assigner/test_assigner_full_flow.py -v
```

### Filter Using Markers

```bash
# Only run tests marked as assigner
pytest -m assigner -v

# Exclude assigner tests
pytest -m "not assigner" -v
```

### Run Specific Model Tests

```bash
# Test specific model
pytest tests/test_endpoints/test_protocol_generation/test_assigner/ -k "qwen3.5-flash" -v
```

## Test Data

### demo_input.json
Contains real test input data:
- Model configuration
- protocol_aimd content (gold triangular nanoplate synthesis protocol)
- protocol_model content (Pydantic model definition)

### demo_output.txt
Contains expected assigner.py output example, showing:
- Standard Assigner class structure
- Correct usage of `@assigner` decorator
- Definition of dependent and assigned fields
- Implementation of calculation logic

## Important Notes

1. **Test Environment**: Ensure tests run in the `masterbrain` conda environment
2. **Mock Strategy**: All tests use Mock objects, no real LLM API calls are made
3. **Timeout Settings**: Tests include timeout handling to prevent infinite waiting
4. **Error Handling**: Tests cover various error situations to ensure robustness
5. **Code Quality**: All generated code undergoes format validation

## Extending Tests

To add new test scenarios:

1. Add new test functions to the appropriate test file
2. Use `@pytest.mark.assigner` marker
3. Use appropriate `@pytest.mark.asyncio` marker for async tests
4. Follow existing Mock patterns
5. Update this README documentation