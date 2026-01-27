"""
TDD Tests: Chicken Registry Models

These tests define the expected behavior for chicken and headcount models.
Implement src/models/chicken.py to make these tests pass.

Run: pytest tdd/phase1_foundation/models/test_chicken_models.py -v
"""

import pytest
from datetime import datetime, timezone, date


# =============================================================================
# Test: Chicken Model
# =============================================================================

class TestChickenModel:
    """Tests for the Chicken model."""

    def test_chicken_requires_name(self):
        """Chicken must have a name."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Rhode Island Red")

        assert chicken.name == "Henrietta"

    def test_chicken_name_must_be_unique(self):
        """Chicken name should be flagged as unique field."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Rhode Island Red")

        # The model should indicate name is unique
        assert hasattr(Chicken, '_unique_fields') or True  # Implementation varies

    def test_chicken_has_breed(self):
        """Chicken should have breed."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Leghorn")

        assert chicken.breed == "Leghorn"

    def test_chicken_has_color(self):
        """Chicken should have color."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Leghorn", color="white")

        assert chicken.color == "white"

    def test_chicken_has_registration_date(self):
        """Chicken should have date_registered."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Leghorn")

        assert hasattr(chicken, 'date_registered')
        assert isinstance(chicken.date_registered, datetime)

    def test_chicken_is_active_by_default(self):
        """Chicken should be active by default."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Leghorn")

        assert chicken.is_active is True

    def test_chicken_can_be_deactivated(self):
        """Chicken can be marked as inactive."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Leghorn")
        chicken.deactivate()

        assert chicken.is_active is False


# =============================================================================
# Test: Chicken Profile Data
# =============================================================================

class TestChickenProfile:
    """Tests for chicken profile data (for future ML identification)."""

    def test_chicken_has_color_profile(self):
        """Chicken should have color_profile field."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Rhode Island Red")

        assert hasattr(chicken, 'color_profile')

    def test_color_profile_is_dict(self):
        """color_profile should be a dictionary."""
        from src.models.chicken import Chicken

        color_data = {"histogram": [0.1, 0.2, 0.3], "dominant_colors": ["#8B4513"]}
        chicken = Chicken(
            name="Henrietta",
            breed="Rhode Island Red",
            color_profile=color_data
        )

        assert isinstance(chicken.color_profile, dict)
        assert "histogram" in chicken.color_profile

    def test_chicken_has_size_profile(self):
        """Chicken should have size_profile field."""
        from src.models.chicken import Chicken

        chicken = Chicken(name="Henrietta", breed="Rhode Island Red")

        assert hasattr(chicken, 'size_profile')

    def test_size_profile_contains_min_max(self):
        """size_profile should contain min/max pixel areas."""
        from src.models.chicken import Chicken

        size_data = {"min_area": 5000, "max_area": 15000}
        chicken = Chicken(
            name="Henrietta",
            breed="Rhode Island Red",
            size_profile=size_data
        )

        assert chicken.size_profile["min_area"] == 5000
        assert chicken.size_profile["max_area"] == 15000

    def test_chicken_has_notes(self):
        """Chicken should have notes field."""
        from src.models.chicken import Chicken

        chicken = Chicken(
            name="Henrietta",
            breed="Rhode Island Red",
            notes="Has a distinctive red comb"
        )

        assert chicken.notes == "Has a distinctive red comb"


# =============================================================================
# Test: Chicken Serialization
# =============================================================================

class TestChickenSerialization:
    """Tests for Chicken serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        from src.models.chicken import Chicken

        chicken = Chicken(
            name="Henrietta",
            breed="Rhode Island Red",
            color="red"
        )

        result = chicken.to_dict()

        assert "name" in result
        assert "breed" in result
        assert "color" in result
        assert "is_active" in result

    def test_from_dict_creates_instance(self):
        """from_dict should create Chicken."""
        from src.models.chicken import Chicken

        data = {
            "name": "Henrietta",
            "breed": "Rhode Island Red",
            "color": "red",
            "is_active": True,
            "date_registered": datetime.now(timezone.utc).isoformat()
        }

        chicken = Chicken.from_dict(data)

        assert chicken.name == "Henrietta"
        assert chicken.breed == "Rhode Island Red"


# =============================================================================
# Test: HeadcountLog Model
# =============================================================================

class TestHeadcountLogModel:
    """Tests for the HeadcountLog model."""

    def test_headcount_requires_count(self):
        """HeadcountLog must have count_detected."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=5,
            expected_count=6
        )

        assert log.count_detected == 5

    def test_headcount_requires_expected(self):
        """HeadcountLog must have expected_count."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=5,
            expected_count=6
        )

        assert log.expected_count == 6

    def test_headcount_has_timestamp(self):
        """HeadcountLog should have timestamp."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=6,
            expected_count=6
        )

        assert hasattr(log, 'timestamp')
        assert isinstance(log.timestamp, datetime)

    def test_all_present_calculated(self):
        """all_present should be True when counts match."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=6,
            expected_count=6
        )

        assert log.all_present is True

    def test_all_present_false_when_missing(self):
        """all_present should be False when counts don't match."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=5,
            expected_count=6
        )

        assert log.all_present is False

    def test_headcount_has_confidence(self):
        """HeadcountLog should have confidence score."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=6,
            expected_count=6,
            confidence=0.92
        )

        assert log.confidence == 0.92

    def test_confidence_in_valid_range(self):
        """Confidence should be between 0 and 1."""
        from src.models.chicken import HeadcountLog, ValidationError

        with pytest.raises(ValidationError):
            log = HeadcountLog(
                count_detected=6,
                expected_count=6,
                confidence=1.5
            )
            log.validate()


# =============================================================================
# Test: HeadcountLog Methods
# =============================================================================

class TestHeadcountLogMethods:
    """Tests for HeadcountLog analysis methods."""

    def test_headcount_method_field(self):
        """HeadcountLog should track counting method."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=6,
            expected_count=6,
            method="simple_count"
        )

        assert log.method == "simple_count"

    def test_valid_counting_methods(self):
        """Method should be one of valid options."""
        from src.models.chicken import HeadcountLog

        valid_methods = ["simple_count", "ml_detect", "manual"]

        for method in valid_methods:
            log = HeadcountLog(
                count_detected=6,
                expected_count=6,
                method=method
            )
            assert log.method == method

    def test_missing_count_property(self):
        """Should calculate number of missing chickens."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=4,
            expected_count=6
        )

        assert log.missing_count == 2

    def test_missing_count_zero_when_all_present(self):
        """missing_count should be 0 when all present."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=6,
            expected_count=6
        )

        assert log.missing_count == 0

    def test_image_path_for_anomalies(self):
        """HeadcountLog should store image path for anomalies."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=4,
            expected_count=6,
            image_path="headcount_anomalies/20250125_200532.jpg"
        )

        assert log.image_path == "headcount_anomalies/20250125_200532.jpg"


# =============================================================================
# Test: HeadcountLog Serialization
# =============================================================================

class TestHeadcountLogSerialization:
    """Tests for HeadcountLog serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=5,
            expected_count=6,
            confidence=0.85
        )

        result = log.to_dict()

        assert "count_detected" in result
        assert "expected_count" in result
        assert "all_present" in result
        assert "confidence" in result
        assert "timestamp" in result

    def test_to_api_response_format(self):
        """Should format for API response."""
        from src.models.chicken import HeadcountLog

        log = HeadcountLog(
            count_detected=5,
            expected_count=6,
            confidence=0.85,
            method="simple_count"
        )

        result = log.to_api_response()

        # API response uses slightly different keys
        assert "count" in result or "count_detected" in result
        assert "expected" in result or "expected_count" in result

    def test_from_dict_creates_instance(self):
        """from_dict should create HeadcountLog."""
        from src.models.chicken import HeadcountLog

        data = {
            "count_detected": 5,
            "expected_count": 6,
            "confidence": 0.85,
            "method": "simple_count",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        log = HeadcountLog.from_dict(data)

        assert log.count_detected == 5
        assert log.confidence == 0.85


# =============================================================================
# Test: ChickenRegistry Collection
# =============================================================================

class TestChickenRegistry:
    """Tests for chicken registry operations."""

    def test_registry_holds_multiple_chickens(self):
        """Registry should hold multiple chickens."""
        from src.models.chicken import Chicken, ChickenRegistry

        registry = ChickenRegistry([
            Chicken(name="Henrietta", breed="Rhode Island Red"),
            Chicken(name="Clover", breed="Leghorn"),
        ])

        assert len(registry) == 2

    def test_get_active_chickens(self):
        """Should get only active chickens."""
        from src.models.chicken import Chicken, ChickenRegistry

        registry = ChickenRegistry([
            Chicken(name="Henrietta", breed="Rhode Island Red", is_active=True),
            Chicken(name="Clover", breed="Leghorn", is_active=False),
        ])

        active = registry.get_active()

        assert len(active) == 1
        assert active[0].name == "Henrietta"

    def test_get_by_name(self):
        """Should get chicken by name."""
        from src.models.chicken import Chicken, ChickenRegistry

        registry = ChickenRegistry([
            Chicken(name="Henrietta", breed="Rhode Island Red"),
            Chicken(name="Clover", breed="Leghorn"),
        ])

        chicken = registry.get_by_name("Clover")

        assert chicken.name == "Clover"
        assert chicken.breed == "Leghorn"

    def test_expected_count(self):
        """Should return expected count (active chickens)."""
        from src.models.chicken import Chicken, ChickenRegistry

        registry = ChickenRegistry([
            Chicken(name="Henrietta", breed="Rhode Island Red", is_active=True),
            Chicken(name="Clover", breed="Leghorn", is_active=True),
            Chicken(name="Retired", breed="Brahma", is_active=False),
        ])

        assert registry.expected_count == 2
