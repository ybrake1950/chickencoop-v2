"""Coverage improvement tests for service modules.

Covers:
- src/services/video_service.py (60% -> 80%+)
- src/services/sensor_service.py (67% -> 80%+)
"""

from unittest.mock import MagicMock

import pytest

from src.services.video_service import VideoService
from src.services.sensor_service import SensorService


class TestVideoServiceGetVideoUrl:
    def test_get_video_url_returns_presigned_url(self):
        video_repo = MagicMock()
        s3_client = MagicMock()
        video_repo.find_by_id.return_value = {"id": 1, "s3_key": "videos/test.mp4"}
        s3_client.generate_presigned_url.return_value = "https://s3.example.com/test.mp4"
        service = VideoService(video_repo=video_repo, s3_client=s3_client)
        url = service.get_video_url(1)
        assert url == "https://s3.example.com/test.mp4"

    def test_get_video_url_returns_none_when_not_found(self):
        video_repo = MagicMock()
        s3_client = MagicMock()
        video_repo.find_by_id.return_value = None
        service = VideoService(video_repo=video_repo, s3_client=s3_client)
        url = service.get_video_url(999)
        assert url is None

    def test_get_video_url_returns_none_without_s3_client(self):
        video_repo = MagicMock()
        video_repo.find_by_id.return_value = {"id": 1, "s3_key": "videos/test.mp4"}
        service = VideoService(video_repo=video_repo, s3_client=None)
        url = service.get_video_url(1)
        assert url is None

    def test_record_video_returns_metadata(self):
        service = VideoService()
        result = service.record_video("cam1", duration=60)
        assert isinstance(result, dict)
        assert result["camera"] == "cam1"
        assert result["duration"] == 60

    def test_record_video_default_duration(self):
        service = VideoService()
        result = service.record_video("cam1")
        assert result["duration"] == 30


class TestSensorServiceProcessReading:
    """Test sensor service pipeline. process_reading takes a dict with
    temperature/humidity keys. Internal attributes use underscore prefix."""

    def _make_service(self, **kwargs):
        defaults = {
            "sensor_repo": MagicMock(),
            "csv_storage": MagicMock(),
            "iot_client": MagicMock(),
            "alert_service": MagicMock(),
        }
        defaults.update(kwargs)
        return SensorService(**defaults)

    def _make_reading(self):
        return {"temperature": 72.0, "humidity": 50.0}

    def test_process_reading_stores_to_csv(self):
        service = self._make_service()
        service.process_reading(self._make_reading())
        service._csv_storage.append_reading.assert_called_once()

    def test_process_reading_csv_failure_continues(self):
        service = self._make_service()
        service._csv_storage.append_reading.side_effect = IOError("disk full")
        result = service.process_reading(self._make_reading())
        assert isinstance(result, dict)

    def test_process_reading_publishes_to_iot(self):
        service = self._make_service()
        service.process_reading(self._make_reading())
        service._iot_client.publish_sensor_reading.assert_called_once()

    def test_process_reading_iot_failure_continues(self):
        service = self._make_service()
        service._iot_client.publish_sensor_reading.side_effect = Exception("connection lost")
        result = service.process_reading(self._make_reading())
        assert isinstance(result, dict)

    def test_process_reading_checks_alerts(self):
        service = self._make_service()
        service.process_reading(self._make_reading())
        service.alert_service.check_and_alert.assert_called_once()

    def test_process_reading_alert_failure_continues(self):
        service = self._make_service()
        service.alert_service.check_and_alert.side_effect = Exception("alert failed")
        result = service.process_reading(self._make_reading())
        assert isinstance(result, dict)

    def test_process_reading_db_failure_logged(self):
        service = self._make_service()
        service.sensor_repo.save.side_effect = Exception("db error")
        result = service.process_reading(self._make_reading())
        assert result["stored_locally"] is False


class TestSensorServiceGetLatestReadings:
    def test_get_latest_returns_readings(self):
        repo = MagicMock()
        reading = MagicMock()
        reading.temperature = 72.0
        reading.humidity = 50.0
        repo.get_latest.return_value = reading
        service = SensorService(sensor_repo=repo)
        result = service.get_latest_readings()
        assert len(result) == 1
        assert result[0]["temperature"] == 72.0

    def test_get_latest_returns_empty_on_none(self):
        repo = MagicMock()
        repo.get_latest.return_value = None
        service = SensorService(sensor_repo=repo)
        result = service.get_latest_readings()
        assert result == []

    def test_get_latest_returns_empty_on_exception(self):
        repo = MagicMock()
        repo.get_latest.side_effect = Exception("db error")
        service = SensorService(sensor_repo=repo)
        result = service.get_latest_readings()
        assert result == []


class TestSensorServiceInit:
    def test_init_creates_repo_from_database(self):
        database = MagicMock()
        service = SensorService(database=database)
        assert service.sensor_repo is not None
