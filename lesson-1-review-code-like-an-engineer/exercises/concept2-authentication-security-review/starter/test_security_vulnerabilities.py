"""Tests for secure authentication.

These tests describe the fixed behaviour. Run them on the starter first: some fail, and each
failing test's docstring says which problem it points at. Fix user_auth.py until they all pass.
The tests create their users with register_user(username, password), which returns the new user's id.
"""

import ast
import inspect

import pytest
import user_auth
from user_auth import UserAuth


class TestBasicSecureAuthentication:
    """Tests for basic secure authentication functionality."""
    
    def test_user_registration_and_login_works(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        
        # Register a new user
        user_id = auth.register_user("testuser", "secure_password_123")
        assert user_id is not None
        assert isinstance(user_id, int)
        
        # Login with correct credentials
        token = auth.login("testuser", "secure_password_123")
        assert token is not None
        assert len(token) > 20  # Should be a secure token
    
    def test_wrong_password_fails(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        auth.register_user("testuser", "correct_password")
        
        # Wrong password should fail
        token = auth.login("testuser", "wrong_password")
        assert token is None
    
    def test_nonexistent_user_fails(self):
        """Test that nonexistent user fails securely."""
        auth = UserAuth()
        
        # Nonexistent user should fail
        token = auth.login("nonexistent", "any_password")
        assert token is None


class TestSQLInjectionPrevention:
    """Tests that SQL injection attacks are blocked."""
    
    def test_sql_injection_in_login_blocked(self):
        """Fails on the starter: no register_user() yet; once it exists, login()'s f-string query lets the injection log in. Passes once fixed."""
        auth = UserAuth()
        auth.register_user("alice", "secure_password")
        
        # These SQL injection attempts should all fail
        sql_injections = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM users --",
            "' OR 1=1 --",
        ]
        
        for injection in sql_injections:
            token = auth.login(injection, "any_password")
            assert token is None, f"SQL injection '{injection}' should be blocked!"


class TestPasswordStorage:
    """Tests that passwords are not stored as typed."""

    def test_password_not_stored_in_plain_text(self):
        """Fails on the starter: no register_user() yet; once it exists, the password is stored as typed. Passes once fixed."""
        auth = UserAuth()
        auth.register_user("hashuser", "Plain-Text-Pass-1")

        rows = auth.db_connection.execute("SELECT * FROM users").fetchall()
        for row in rows:
            assert "Plain-Text-Pass-1" not in [str(value) for value in row], \
                "The password is stored as typed; store a hash of it instead"


class TestSecureTokenGeneration:
    """Tests for secure token generation."""
    
    def test_tokens_are_unique(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        auth.register_user("testuser", "password")
        
        # Generate multiple tokens
        tokens = []
        for _ in range(10):
            token = auth.login("testuser", "password")
            tokens.append(token)
        
        # All tokens should be unique
        assert len(set(tokens)) == len(tokens), "All tokens should be unique"
    
    def test_tokens_have_good_length(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        auth.register_user("testuser", "password")
        
        token = auth.login("testuser", "password")
        assert len(token) >= 32, "Tokens should be at least 32 characters"

    def test_tokens_use_secrets_module(self):
        """Fails on the starter: tokens come from the predictable random module. Passes once fixed."""
        tree = ast.parse(inspect.getsource(user_auth))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert "random" not in imported, "Session tokens must not come from the random module"
        assert "secrets" in imported, "Generate session tokens with the secrets module"


class TestInputValidation:
    """Tests for basic input validation."""
    
    def test_empty_username_handled(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        
        try:
            auth.register_user("", "valid_password")
            # If it doesn't raise an error, that's also acceptable
        except ValueError:
            # This is the preferred behavior
            pass
    
    def test_empty_password_handled(self):
        """Fails on the starter: no register_user() to store a new user. Passes once fixed."""
        auth = UserAuth()
        
        try:
            auth.register_user("validuser", "")
            # If it doesn't raise an error, that's also acceptable
        except ValueError:
            # This is the preferred behavior
            pass
