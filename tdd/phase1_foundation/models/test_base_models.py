"""
TDD Tests: Base Data Models

These tests define the expected behavior for base model classes.
Implement src/models/base.py to make these tests pass.

Run: pytest tdd/phase1_foundation/models/test_base_models.py -v
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any


# =============================================================================
# Test: Base Model Class
# =============================================================================

class TestBaseModel:
    """Tests for the base model class functionality."""

    def test_base_model_can_be_instantiated(self):
        """Base model should be instantiable."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert model is not None

    def test_base_model_has_created_at(self):
        """Base model should have created_at timestamp."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert hasattr(model, 'created_at')
        assert isinstance(model.created_at, datetime)

    def test_base_model_created_at_is_utc(self):
        """created_at should be in UTC timezone."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert model.created_at.tzinfo == timezone.utc

    def test_base_model_to_dict_returns_dict(self):
        """to_dict should return a dictionary."""
        from src.models.base import BaseModel

        model = BaseModel()
        result = model.to_dict()

        assert isinstance(result, dict)

    def test_base_model_from_dict_creates_instance(self):
        """from_dict should create model from dictionary."""
        from src.models.base import BaseModel

        data = {"created_at": datetime.now(timezone.utc).isoformat()}
        model = BaseModel.from_dict(data)

        assert isinstance(model, BaseModel)


# =============================================================================
# Test: Model Validation
# =============================================================================

class TestModelValidation:
    """Tests for model validation functionality."""

    def test_validate_returns_true_for_valid_model(self):
        """validate should return True for valid model."""
        from src.models.base import BaseModel

        model = BaseModel()
        result = model.validate()

        assert result is True

    def test_validation_errors_returns_list(self):
        """validation_errors should return list of errors."""
        from src.models.base import BaseModel

        model = BaseModel()
        errors = model.validation_errors()

        assert isinstance(errors, list)

    def test_is_valid_property(self):
        """is_valid property should indicate validity."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert isinstance(model.is_valid, bool)


# =============================================================================
# Test: Model Serialization
# =============================================================================

class TestModelSerialization:
    """Tests for model serialization."""

    def test_to_json_returns_string(self):
        """to_json should return JSON string."""
        from src.models.base import BaseModel
        import json

        model = BaseModel()
        result = model.to_json()

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_from_json_creates_instance(self):
        """from_json should create model from JSON string."""
        from src.models.base import BaseModel
        import json

        json_str = json.dumps({"created_at": datetime.now(timezone.utc).isoformat()})
        model = BaseModel.from_json(json_str)

        assert isinstance(model, BaseModel)

    def test_serialization_roundtrip(self):
        """Serializing and deserializing should preserve data."""
        from src.models.base import BaseModel

        original = BaseModel()
        json_str = original.to_json()
        restored = BaseModel.from_json(json_str)

        assert restored.created_at == original.created_at


# =============================================================================
# Test: Model Equality
# =============================================================================

class TestModelEquality:
    """Tests for model equality comparison."""

    def test_models_with_same_data_are_equal(self):
        """Models with same data should be equal."""
        from src.models.base import BaseModel

        timestamp = datetime.now(timezone.utc)
        model1 = BaseModel()
        model1.created_at = timestamp
        model2 = BaseModel()
        model2.created_at = timestamp

        assert model1 == model2

    def test_models_with_different_data_are_not_equal(self):
        """Models with different data should not be equal."""
        from src.models.base import BaseModel
        from datetime import timedelta

        model1 = BaseModel()
        model2 = BaseModel()
        model2.created_at = model1.created_at + timedelta(seconds=1)

        assert model1 != model2

    def test_model_not_equal_to_none(self):
        """Model should not be equal to None."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert model != None  # noqa: E711

    def test_model_not_equal_to_different_type(self):
        """Model should not be equal to different type."""
        from src.models.base import BaseModel

        model = BaseModel()

        assert model != "not a model"
        assert model != 42


# =============================================================================
# Test: Model Hashing
# =============================================================================

class TestModelHashing:
    """Tests for model hashing (for use in sets/dicts)."""

    def test_model_is_hashable(self):
        """Model should be hashable."""
        from src.models.base import BaseModel

        model = BaseModel()

        # Should not raise
        hash_value = hash(model)
        assert isinstance(hash_value, int)

    def test_equal_models_have_same_hash(self):
        """Equal models should have the same hash."""
        from src.models.base import BaseModel

        timestamp = datetime.now(timezone.utc)
        model1 = BaseModel()
        model1.created_at = timestamp
        model2 = BaseModel()
        model2.created_at = timestamp

        if model1 == model2:
            assert hash(model1) == hash(model2)


# =============================================================================
# Test: Model String Representation
# =============================================================================

class TestModelStringRepresentation:
    """Tests for model string representation."""

    def test_str_returns_readable_string(self):
        """__str__ should return readable string."""
        from src.models.base import BaseModel

        model = BaseModel()
        result = str(model)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_repr_returns_debug_string(self):
        """__repr__ should return debug-friendly string."""
        from src.models.base import BaseModel

        model = BaseModel()
        result = repr(model)

        assert isinstance(result, str)
        assert "BaseModel" in result


# =============================================================================
# Test: Model Copy
# =============================================================================

class TestModelCopy:
    """Tests for model copying."""

    def test_copy_creates_new_instance(self):
        """copy should create a new instance."""
        from src.models.base import BaseModel

        original = BaseModel()
        copied = original.copy()

        assert copied is not original
        assert isinstance(copied, BaseModel)

    def test_copy_preserves_data(self):
        """copy should preserve all data."""
        from src.models.base import BaseModel

        original = BaseModel()
        copied = original.copy()

        assert copied.created_at == original.created_at

    def test_modifying_copy_does_not_affect_original(self):
        """Modifying copy should not affect original."""
        from src.models.base import BaseModel
        from datetime import timedelta

        original = BaseModel()
        original_timestamp = original.created_at

        copied = original.copy()
        copied.created_at = copied.created_at + timedelta(hours=1)

        assert original.created_at == original_timestamp
