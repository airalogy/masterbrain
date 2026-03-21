# Vision (Image Recognition) Tests

This directory contains the complete test suite for Vision functionality, modeled after the `test_stt` structure.

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all Vision tests
pytest tests/test_endpoints/test_chat/test_qa/test_vision/ -v -m vision

# Run specific test files
pytest tests/test_endpoints/test_chat/test_qa/test_vision/test_router.py -v
pytest tests/test_endpoints/test_chat/test_qa/test_vision/test_recognize.py -v
pytest tests/test_endpoints/test_chat/test_qa/test_vision/test_vision_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_chat/test_qa/test_vision/ -v -k "gpt-4o"
pytest tests/test_endpoints/test_chat/test_qa/test_vision/ -v -k "qwen-vl"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_chat/test_qa/test_vision/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_chat/test_qa/test_vision/test_router.py::test_vision_recognition_success -v

# Use parameterized tests
pytest tests/test_endpoints/test_chat/test_qa/test_vision/test_recognize.py::test_recognize_image_success -v
```

### Method 3: Run in masterbrain conda environment

```bash
# Activate masterbrain environment first
conda activate masterbrain

# Then run tests as above
pytest tests/test_endpoints/test_chat/test_qa/test_vision/ -v -m vision
```

## Test Structure

- `conftest.py` - Test configuration and fixtures for vision tests
- `test_router.py` - Tests for the vision router endpoints  
- `test_recognize.py` - Tests for image recognition functions
- `test_vision_full_flow.py` - End-to-end tests for complete vision pipeline

## Test Data

The tests use minimal sample image data:
- PNG format: 1x1 pixel transparent PNG
- JPEG format: 1x1 pixel JPEG
- Base64 encoded for API testing
