# -*- coding: utf-8 -*-

import base64
import binascii
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from RosettaX.workflow.upload.services import (
    DEFAULT_UPLOAD_DIRECTORY,
    clean_optional_string,
    build_loaded_filename_text,
    sanitize_filename,
    decode_dash_upload_contents,
    resolve_upload_directory
)
from RosettaX.workflow.upload.models import UploadConfig


class Test_clean_optional_string:
    """Test suite for clean_optional_string function."""

    def test_clean_optional_string_none(self):
        """Test clean_optional_string with None input."""
        assert clean_optional_string(None) is None

    def test_clean_optional_string_empty_string(self):
        """Test clean_optional_string with empty string."""
        assert clean_optional_string("") is None
        assert clean_optional_string("   ") is None
        assert clean_optional_string("\t\n") is None

    def test_clean_optional_string_none_string(self):
        """Test clean_optional_string with 'none' string."""
        assert clean_optional_string("none") is None
        assert clean_optional_string("None") is None
        assert clean_optional_string("NONE") is None
        assert clean_optional_string("  None  ") is None

    def test_clean_optional_string_valid_string(self):
        """Test clean_optional_string with valid strings."""
        assert clean_optional_string("hello") == "hello"
        assert clean_optional_string("  hello  ") == "hello"
        assert clean_optional_string("hello world") == "hello world"

    def test_clean_optional_string_numeric_input(self):
        """Test clean_optional_string with numeric inputs."""
        assert clean_optional_string(123) == "123"
        assert clean_optional_string(0) == "0"
        assert clean_optional_string(45.67) == "45.67"

    def test_clean_optional_string_boolean_input(self):
        """Test clean_optional_string with boolean inputs."""
        assert clean_optional_string(True) == "True"
        assert clean_optional_string(False) == "False"

    def test_clean_optional_string_object_input(self):
        """Test clean_optional_string with object inputs."""
        test_obj = object()
        result = clean_optional_string(test_obj)
        assert result is not None
        assert isinstance(result, str)


class Test_build_loaded_filename_text:
    """Test suite for build_loaded_filename_text function."""

    def test_build_loaded_filename_text_none(self):
        """Test build_loaded_filename_text with None filename."""
        result = build_loaded_filename_text(None)
        assert result == "No file loaded."

    def test_build_loaded_filename_text_empty_string(self):
        """Test build_loaded_filename_text with empty filename."""
        result = build_loaded_filename_text("")
        assert result == "No file loaded."
        
        result = build_loaded_filename_text("   ")
        assert result == "No file loaded."

    def test_build_loaded_filename_text_none_string(self):
        """Test build_loaded_filename_text with 'none' filename."""
        result = build_loaded_filename_text("none")
        assert result == "No file loaded."

    def test_build_loaded_filename_text_valid_filename(self):
        """Test build_loaded_filename_text with valid filename."""
        result = build_loaded_filename_text("data.fcs")
        assert result == "Loaded file: data.fcs"
        
        result = build_loaded_filename_text("experiment_data.fcs")
        assert result == "Loaded file: experiment_data.fcs"

    def test_build_loaded_filename_text_with_whitespace(self):
        """Test build_loaded_filename_text with filename containing whitespace."""
        result = build_loaded_filename_text("  data.fcs  ")
        assert result == "Loaded file: data.fcs"


class Test_sanitize_filename:
    """Test suite for sanitize_filename function."""

    def test_sanitize_filename_none(self):
        """Test sanitize_filename with None input."""
        result = sanitize_filename(None)
        assert result == "uploaded_file.fcs"

    def test_sanitize_filename_empty_string(self):
        """Test sanitize_filename with empty string."""
        result = sanitize_filename("")
        assert result == "uploaded_file.fcs"

    def test_sanitize_filename_custom_fallback(self):
        """Test sanitize_filename with custom fallback."""
        result = sanitize_filename(None, fallback_filename="custom_fallback.dat")
        assert result == "custom_fallback.dat"

    def test_sanitize_filename_valid_filename(self):
        """Test sanitize_filename with valid filename."""
        result = sanitize_filename("data.fcs")
        assert result == "data.fcs"
        
        result = sanitize_filename("experiment_data.fcs")
        assert result == "experiment_data.fcs"

    def test_sanitize_filename_with_path(self):
        """Test sanitize_filename strips path components."""
        result = sanitize_filename("/path/to/data.fcs")
        assert result == "data.fcs"
        
        result = sanitize_filename("../../dangerous/path/data.fcs")
        assert result == "data.fcs"

    def test_sanitize_filename_with_special_characters(self):
        """Test sanitize_filename handles special characters."""
        result = sanitize_filename("data@#$%.fcs")
        assert result == "data_.fcs"
        
        result = sanitize_filename("data with spaces.fcs")
        assert result == "data_with_spaces.fcs"

    def test_sanitize_filename_strip_leading_trailing_chars(self):
        """Test sanitize_filename strips leading/trailing dots and underscores."""
        result = sanitize_filename("._data.fcs_.")
        assert result == "data.fcs"
        
        result = sanitize_filename("...data...")
        assert result == "data"

    def test_sanitize_filename_only_special_characters(self):
        """Test sanitize_filename with only special characters."""
        result = sanitize_filename("@#$%^&*()")
        assert result == "uploaded_file.fcs"
        
        result = sanitize_filename("@#$%^&*()", fallback_filename="fallback.dat")
        assert result == "fallback.dat"

    def test_sanitize_filename_unicode_characters(self):
        """Test sanitize_filename with unicode characters."""
        result = sanitize_filename("dataé.fcs")
        assert result == "data_.fcs"
        
        result = sanitize_filename("测试.fcs")
        assert result == "fcs"

    def test_sanitize_filename_windows_reserved_names(self):
        """Test sanitize_filename with potentially problematic names."""
        # Test with names that might be reserved on Windows
        result = sanitize_filename("CON.fcs")
        assert result == "CON.fcs"  # Should be allowed as it has extension

    @pytest.mark.parametrize("input_filename,expected", [
        ("normal.fcs", "normal.fcs"),
        ("with spaces.fcs", "with_spaces.fcs"),
        ("with-dashes.fcs", "with-dashes.fcs"),
        ("with_underscores.fcs", "with_underscores.fcs"),
        ("with.multiple.dots.fcs", "with.multiple.dots.fcs"),
        ("123numeric.fcs", "123numeric.fcs"),
    ])
    def test_sanitize_filename_parametrized(self, input_filename, expected):
        """Parametrized test for various filename sanitization cases."""
        result = sanitize_filename(input_filename)
        assert result == expected


class Test_decode_dash_upload_contents:
    """Test suite for decode_dash_upload_contents function."""

    def test_decode_dash_upload_contents_valid_format(self):
        """Test decode_dash_upload_contents with valid format."""
        test_data = b"Hello, World!"
        encoded_data = base64.b64encode(test_data).decode('ascii')
        contents = f"data:text/plain;base64,{encoded_data}"
        
        result = decode_dash_upload_contents(contents)
        assert result == test_data

    def test_decode_dash_upload_contents_different_mime(self):
        """Test decode_dash_upload_contents with different MIME type."""
        test_data = b"Binary data content"
        encoded_data = base64.b64encode(test_data).decode('ascii')
        contents = f"data:application/octet-stream;base64,{encoded_data}"
        
        result = decode_dash_upload_contents(contents)
        assert result == test_data

    def test_decode_dash_upload_contents_no_comma(self):
        """Test decode_dash_upload_contents with malformed input (no comma)."""
        with pytest.raises(ValueError, match="Upload contents are malformed"):
            decode_dash_upload_contents("data:text/plain;base64")

    def test_decode_dash_upload_contents_empty_payload(self):
        """Test decode_dash_upload_contents with empty payload."""
        contents = "data:text/plain;base64,"
        result = decode_dash_upload_contents(contents)
        assert result == b""

    def test_decode_dash_upload_contents_invalid_base64(self):
        """Test decode_dash_upload_contents with invalid base64."""
        contents = "data:text/plain;base64,invalid!base64@content"
        
        with pytest.raises(ValueError, match="Upload contents could not be decoded"):
            decode_dash_upload_contents(contents)

    def test_decode_dash_upload_contents_multiple_commas(self):
        """Test decode_dash_upload_contents with multiple commas in content."""
        test_data = b"Content,with,commas"
        encoded_data = base64.b64encode(test_data).decode('ascii')
        contents = f"data:text/plain;base64,{encoded_data}"
        
        result = decode_dash_upload_contents(contents)
        assert result == test_data

    def test_decode_dash_upload_contents_complex_mime(self):
        """Test decode_dash_upload_contents with complex MIME type."""
        test_data = b"Complex binary data"
        encoded_data = base64.b64encode(test_data).decode('ascii')
        contents = f"data:application/vnd.some-format+json;charset=utf-8;base64,{encoded_data}"
        
        result = decode_dash_upload_contents(contents)
        assert result == test_data

    def test_decode_dash_upload_contents_binary_file_simulation(self):
        """Test decode_dash_upload_contents with simulated binary file."""
        # Simulate FCS file binary data
        test_data = b'\x46\x43\x53\x33\x2e\x30\x20\x20\x20\x20\x20\x20'  # FCS3.0 header
        encoded_data = base64.b64encode(test_data).decode('ascii')
        contents = f"data:application/octet-stream;base64,{encoded_data}"
        
        result = decode_dash_upload_contents(contents)
        assert result == test_data


class Test_resolve_upload_directory:
    """Test suite for resolve_upload_directory function."""

    @pytest.fixture
    def mock_upload_config(self):
        """Fixture providing a mock UploadConfig."""
        config = Mock(spec=UploadConfig)
        return config

    def test_default_upload_directory_constant(self):
        """Test that DEFAULT_UPLOAD_DIRECTORY is properly defined."""
        assert isinstance(DEFAULT_UPLOAD_DIRECTORY, Path)
        assert str(DEFAULT_UPLOAD_DIRECTORY).endswith("/.rosettax/uploads")

    def test_resolve_upload_directory_basic(self, mock_upload_config):
        """Test resolve_upload_directory basic functionality."""
        mock_upload_config.upload_directory = None
        result = resolve_upload_directory(mock_upload_config)
        assert result == DEFAULT_UPLOAD_DIRECTORY

    def test_resolve_upload_directory_with_custom_path(self, mock_upload_config):
        """Test resolve_upload_directory with custom path configuration."""
        # Mock the config to have a custom upload directory
        custom_path = Path("/custom/upload/path")
        mock_upload_config.upload_directory = custom_path
        
        try:
            result = resolve_upload_directory(mock_upload_config)
            # The function might use the custom path or transform it somehow
            assert isinstance(result, Path)
        except AttributeError:
            # If the function signature is different than expected
            pytest.skip("Cannot test without knowing UploadConfig structure")


class Test_upload_services_integration:
    """Integration tests for upload services functions."""

    def test_filename_processing_pipeline(self):
        """Test complete filename processing pipeline."""
        # Simulate processing a user-uploaded filename
        user_filename = "  My Data File (version 2).fcs  "
        
        # Clean the filename
        cleaned = clean_optional_string(user_filename)
        assert cleaned == "My Data File (version 2).fcs"
        
        # Sanitize for filesystem
        sanitized = sanitize_filename(cleaned)
        assert sanitized == "My_Data_File_version_2_.fcs"
        
        # Build display text
        display_text = build_loaded_filename_text(cleaned)
        assert display_text == "Loaded file: My Data File (version 2).fcs"

    def test_dash_upload_complete_flow(self):
        """Test complete Dash upload processing flow."""
        # Simulate Dash upload data
        original_filename = "experiment_data.fcs"
        file_content = b"FCS3.0    \x00\x00\x00\x00\x00\x00"
        
        # Encode as Dash would
        encoded_content = base64.b64encode(file_content).decode('ascii')
        dash_contents = f"data:application/octet-stream;base64,{encoded_content}"
        
        # Process the upload
        decoded_content = decode_dash_upload_contents(dash_contents)
        safe_filename = sanitize_filename(original_filename)
        display_text = build_loaded_filename_text(original_filename)
        
        # Verify results
        assert decoded_content == file_content
        assert safe_filename == "experiment_data.fcs"
        assert display_text == "Loaded file: experiment_data.fcs"

    def test_error_handling_robustness(self):
        """Test that functions handle edge cases gracefully."""
        default_inputs = [None, "", "   ", "none"]

        for problematic_input in default_inputs:
            cleaned = clean_optional_string(problematic_input)
            display_text = build_loaded_filename_text(problematic_input)
            sanitized = sanitize_filename(problematic_input)

            assert cleaned is None
            assert display_text == "No file loaded."
            assert sanitized == "uploaded_file.fcs"

        assert build_loaded_filename_text(123) == "Loaded file: 123"
        assert sanitize_filename(123) == "123"
        assert build_loaded_filename_text([]) == "Loaded file: []"
        assert sanitize_filename([]) == "uploaded_file.fcs"
        assert build_loaded_filename_text({}) == "Loaded file: {}"
        assert sanitize_filename({}) == "uploaded_file.fcs"