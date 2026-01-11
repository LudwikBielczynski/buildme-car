# Test Documentation

## Running the Tests

### Install test dependencies

```bash
uv sync --group test
```

### Run all tests

```bash
uv run pytest
```

### Run specific test file

```bash
uv run pytest tests/test_base_camera.py
```

### Run specific test class

```bash
uv run pytest tests/test_base_camera.py::TestStreamingStartStop
```

### Run specific test

```bash
uv run pytest tests/test_base_camera.py::TestStreamingStartStop::test_start_streaming_sets_flag
```

### Run with verbose output

```bash
uv run pytest -v
```

### Run with output (including print statements)

```bash
uv run pytest -v -s
```

## Test Structure

### `test_base_camera.py`

Comprehensive tests for the BaseCamera class to diagnose streaming issues:

1. **TestCameraEvent**: Tests the CameraEvent synchronization mechanism
   - Event creation and initialization
   - Wait/signal functionality
   - Multi-thread signaling

2. **TestBaseCameraInitialization**: Tests camera initialization
   - Initial state verification
   - Singleton pattern verification

3. **TestStreamingStartStop**: Tests streaming lifecycle
   - Starting and stopping streams
   - Thread management
   - Multiple start/stop cycles

4. **TestFrameRetrieval**: Tests frame generation and retrieval
   - Frame availability
   - Frame updates
   - Blocking behavior

5. **TestThreadSafety**: Tests concurrent access
   - Multiple threads retrieving frames
   - Thread safety of operations

6. **TestStreamingIssues**: Specific tests to diagnose streaming problems
   - Streaming startup timing
   - Frame availability timing
   - Event signaling
   - Stop/start recovery

7. **TestIntegrationScenarios**: Real-world usage patterns
   - Web streaming simulation
   - Toggle streaming scenarios

## Common Issues Diagnosed

The tests specifically check for:

1. **Streaming doesn't start**: `test_streaming_starts_immediately`
2. **No frames received**: `test_first_frame_available_quickly`
3. **Streaming doesn't stop**: `test_stop_streaming_clears_flag`
4. **Frames not updating**: `test_get_frame_updates_with_new_frames`
5. **Thread deadlock**: `test_get_frame_before_streaming_blocks`
6. **Event signaling failure**: `test_event_signaling_works`
7. **Cannot restart after stop**: `test_camera_recovers_from_stop_start`

## Expected Results

All tests should pass if the BaseCamera implementation is correct. Any failures will indicate specific issues with the streaming mechanism.

## Debugging Streaming Issues

If streaming is not working in production:

1. Run the full test suite to identify failing tests
2. Check the specific test that fails - it will indicate the problem area
3. Run with `-s` flag to see print output: `pytest -v -s tests/test_base_camera.py`
4. Add debugging output to your Camera implementation
5. Check if the singleton pattern is causing issues with multiple camera instances
