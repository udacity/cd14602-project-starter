# Concept 5: Database Operations Review

## Exercise Overview

Review database operations code that demonstrates basic SQL injection vulnerabilities and simple structural issues. This builds on the security awareness from Concept 2.

## Learning Objectives

- Identify SQL injection vulnerabilities
- Recognize basic input validation issues  
- Apply systematic code review skills
- Understand database security basics

## Instructions

### Step 1: Read the Code Before Running Tests
1. **Open** `starter/database_manager.py` and read the database functions
2. **Note** how each SQL query is built, and where user input goes into it

### Step 2: Run Tests to See the Issues
```bash
cd concept5-database-operations-review/starter
python -m pytest test_database_security.py -v
```

**Expected Output:**
- 9 of the 14 tests fail on this code: each failing test's docstring names the problem it points at
- The 5 that pass already work and must keep passing

### Step 3: Review the Code
1. **Open** `starter/database_manager.py` and review the functions
2. **Apply** the engineering code review framework:
   - Structure & Organization
   - Naming & Clarity
   - Error Handling
   - Security Issues
3. **Document** your findings using the template below

### Step 4: Fix the Code, Then Compare With the Solution
Use Claude Code to fix `starter/database_manager.py` until all 14 tests pass. The tests expect:
- parameterized queries (`?` placeholders) instead of f-strings
- `ValueError` with these messages: "Database path cannot be empty", "Email must be a non-empty string", "Name must be a non-empty string", "User ID must be a positive integer"
- `update_user_email()` returning the number of rows it changed

Then run the solution's tests, the same tests, to compare.
In the Udacity workspace, the `solution` folder sits next to `starter`:
```bash
cd ../solution
python -m pytest test_secure_database.py -v
```

**Expected Output:**
- All 14 tests pass: the same tests your fixed starter passes
- SQL injection is now blocked
- Notice improved parameterized queries

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

**Security Issues:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

### Specific Recommendations

1. **SQL Injection:** [Your recommendations]
2. **Input Validation:** [Your recommendations]
3. **Connection Management:** [Your recommendations]
4. **Error Handling:** [Your recommendations]

### Overall Assessment

- **Quality Rating:** Poor / Fair / Good / Excellent
- **Security Rating:** Critical Risk / High Risk / Medium Risk / Low Risk
- **Recommendation:** Accept / Modify / Reject
- **Reasoning:** [Your explanation]

## Key Learning Points

- SQL injection occurs when user input is directly concatenated into queries
- Parameterized queries prevent SQL injection attacks
- Input validation should happen before database operations
- Database connections should be properly managed and closed

## Common Issues to Look For

1. **String concatenation** in SQL queries instead of parameterized queries
2. **No input validation** for user-provided data
3. **Missing error handling** for database operations
4. **Connection leaks** from unclosed database connections
5. **Generic exception handling** that hides specific database errors

After completing your review, check the solution to see the improved version with parameterized queries, proper input validation, and secure database practices.