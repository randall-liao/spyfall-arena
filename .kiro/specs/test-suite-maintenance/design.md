# Design Document

## Overview

This design addresses the failing test in `test_llm_client_factory.py` and establishes practices for test suite maintenance. The failing test is due to API changes in the LLMClientFactory that now requires a `provider` parameter.

## Problem Analysis

### Failing Test Details

**File**: `tests/llm/test_llm_client_factory.py`

**Issue**: The test file already includes the `provider` parameter in test calls, but there may be additional tests or edge cases that need updating based on recent changes.

**Root Cause**: The LLMClientFactory API evolved to support multiple providers (OpenRouter, Google AI Studio), requiring explicit provider specification.

### Current Test Structure

```python
class TestLLMClientFactory(unittest.TestCase):
    def setUp(self):
        self.mock_api_key_manager = MagicMock(spec=ApiKeyManager)
        self.factory = LLMClientFactory(self.mock_api_key_manager)

    def test_create_openai_client(self):
        # Uses provider=LLMProvider.OPEN_ROUTER
        ...

    def test_create_gemini_client(self):
        # Uses provider=LLMProvider.GOOGLE_AI_STUDIO
        ...
```

## Solution Design

### 1. Diagnose Failing Test

Run the test suite to identify the exact failure:
```bash
poetry run pytest tests/llm/test_llm_client_factory.py -v
```

### 2. Fix Strategy

Based on the phase one report, the test may be failing due to:
1. Missing `provider` argument in some test cases
2. Mock setup not matching current API
3. Changes to factory constructor signature

### 3. Test Verification

After fixing, verify:
- All tests in the file pass
- No regressions in other test files
- Coverage is maintained

## Testing Strategy

### Diagnostic Steps

1. Run failing test in isolation
2. Examine error message and stack trace
3. Compare test expectations with current implementation
4. Update test to match current API

### Verification Steps

1. Run full test suite
2. Generate coverage report
3. Verify no coverage regression

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `tests/llm/test_llm_client_factory.py` | Modify | Fix failing test(s) |
