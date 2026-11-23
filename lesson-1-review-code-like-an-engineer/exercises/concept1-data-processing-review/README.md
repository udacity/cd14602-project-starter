# Concept 1: Data Processing Review

## Exercise Overview

Review a data processing function that demonstrates common code quality issues including magic numbers, poor naming conventions, and lack of error handling.

## Learning Objectives

- Identify structural and organizational issues
- Recognize poor naming conventions
- Spot missing error handling
- Understand the importance of avoiding magic numbers

## Instructions

### Step 1: Read the Code Before Running Tests
1. **Open** `starter/data_processor.py` and read the `process_data()` function without changing it
2. **Note** what the function appears to do

### Step 2: Run Tests to See the Issues
```bash
cd concept1-data-processing-review/starter
pytest test_data_processor.py -v
```

**Expected Output:**
- 9 of the 12 tests fail on this code: each failing test's docstring names the problem it points at
- The 3 that pass (empty list, no active items, zero value) already work and must keep passing

### Step 3: Review the Code
1. **Open** `starter/data_processor.py` and review the function
2. **Apply** the engineering code review framework:
   - Structure & Organization
   - Naming & Clarity
   - Error Handling
   - Testability
3. **Document** your findings using the template below

### Step 4: Fix the Code, Then Compare With the Solution
Use Claude Code to fix `starter/data_processor.py` until all 12 tests pass. The tests expect:
- `MULTIPLIER` and `MAX_VALUE` constants in place of 1.2 and 100
- `ValueError("Input data must be a list")` for input that is not a list, `None` included
- items missing a field skipped, so one bad item no longer stops the run

Then run the solution's tests, the same tests, to compare.
In the Udacity workspace, the `solution` folder sits next to `starter`:
```bash
cd ../solution
pytest test_data_processor.py -v
```

**Expected Output:**
- All 12 tests pass: the same tests your fixed starter passes
- Error handling now works gracefully
- Notice improved testability with constants

### Step 5: Compare and Learn
4. **Compare** your analysis with the improved code

## Review Template

### Issues Found

**Structure & Organization:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

**Naming & Clarity:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

**Error Handling:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

**Testability:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

### Specific Recommendations

1. **Magic Numbers:** [Your recommendations]
2. **Variable Naming:** [Your recommendations]
3. **Error Handling:** [Your recommendations]
4. **Function Design:** [Your recommendations]

### Overall Assessment

- **Quality Rating:** Poor / Fair / Good / Excellent
- **Recommendation:** Accept / Modify / Reject
- **Reasoning:** [Your explanation]

## Key Learning Points

- Magic numbers make code unmaintainable
- Poor variable names reduce code readability
- Missing error handling leads to runtime failures
- Functions should have single, clear responsibilities

## Common Issues to Look For

1. **Magic numbers** (1.2, 100) without explanation
2. **Generic variable names** ('temp', 'data')
3. **No input validation** for missing keys
4. **Mixed responsibilities** in single function
5. **Hard-coded values** scattered throughout

After completing your review, check the solution to see the improved version with proper constants, descriptive names, comprehensive error handling, and separated concerns.