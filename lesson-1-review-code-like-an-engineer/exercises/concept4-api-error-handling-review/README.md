# Concept 4: API Error Handling Review

## Learning Objective
Learn to identify and fix basic error handling issues in API client code, focusing on network errors, HTTP status codes, and user-friendly error messages.

## Background
API clients need proper error handling to provide good user experience and prevent crashes. Common issues include:
- Unhandled network timeouts and connection errors
- Poor HTTP status code handling  
- Returning None without explanation
- Missing input validation

## Exercise Structure

### Starter Code (`starter/`)
- **File**: `api_client.py` - Simple API client with error handling problems
- **Issues**: Network errors crash the program, HTTP failures return None, no input validation
- **Test File**: `test_api_errors.py` - Tests of the fixed behaviour: 17 of the 19 fail on this code, and each failing test's docstring names the problem it points at

### Solution Code (`solution/`, in the Udacity workspace)
- **File**: `api_client.py` - Fixed API client with proper error handling
- **Improvements**: Try/catch blocks, HTTP status checking, structured error responses, input validation
- **Test File**: `test_api_improvements.py` - The same 19 tests, all passing

## How to Run

### Test the Starter Code (Shows Problems)
```bash
cd starter/
pytest test_api_errors.py -v
```

17 of the 19 tests fail. Use Claude Code to fix `starter/api_client.py` until all 19 pass. The tests mock `requests.get()` and `requests.put()`, so call those, and expect:
- `ValueError` with these messages: "Base URL cannot be empty", "API key cannot be empty", "User ID cannot be empty", "Data must be a non-empty dictionary"
- `get_user_data()` returning the user's data on a 200, and otherwise a dictionary with an `"error"` message that says what went wrong: "not found" (404), "unauthorized" and "api key" (401), "server error" (500), the status code for any other, "timed out", "connect" or "Request failed" for network errors
- `update_user()` returning `{"success": True, "message": ...}` with "updated" in the message, or `{"success": False, "error": ...}`, and sending the data with `json=` and a `Content-Type: application/json` header

### Test the Solution Code (Shows Fixes)
In the Udacity workspace, the `solution` folder sits next to `starter`:
```bash
cd ../solution/
python api_client.py
pytest test_api_improvements.py -v
```

## Key Issues to Find

### 1. Network Error Handling
- **Problem**: Network timeouts and connection errors crash the program
- **Fix**: Use try/catch blocks to handle requests exceptions gracefully

### 2. HTTP Status Code Handling
- **Problem**: Only checks for 200, returns None for all other status codes
- **Fix**: Check for common status codes (404, 401, 500) and return helpful error messages

### 3. Error Information
- **Problem**: Functions return None without explaining what went wrong
- **Fix**: Return structured responses with error details

### 4. Input Validation
- **Problem**: No validation of parameters (empty URLs, user IDs, etc.)
- **Fix**: Add basic validation with clear error messages

## Code Review Questions

When reviewing the starter code, consider:

1. **Error Handling**: What happens when network requests fail?
2. **Status Codes**: How are different HTTP response codes handled?
3. **User Experience**: Do users get helpful error messages?
4. **Input Validation**: Are parameters validated before use?
5. **Return Values**: Do functions return useful information about failures?

## Expected Learning Outcomes

After completing this exercise, you should be able to:
- Identify missing network error handling in API clients
- Recognize poor HTTP status code handling patterns
- Implement try/catch blocks for network operations
- Design user-friendly error response structures
- Add basic input validation to API methods