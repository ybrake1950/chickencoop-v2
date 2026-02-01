"""Coverage improvement tests for camera modules.

Covers:
- src/hardware/camera/interface.py (69% -> 80%+)
- src/hardware/camera/factory.py (72% -> 80%+)
"""

import pytest

from src.hardware.camera.interface import Camera
from src.hardware.camera.factory import CameraFactory, MockCamera, USBCamera


class TestCameraInterfaceCoverage:
    def test_stop_recording_raises_not_implemented(self):
        camera = Camera()
        with pytest.raises(NotImplementedError):
            camera.stop_recording()

    def test_is_available_raises_not_implemented(self):
        camera = Camera()
        with pytest.raises(NotImplementedError):
            camera.is_available()


class TestMockCameraCoverage:
    def test_capture_returns_none(self):
        camera = MockCamera()
        result = camera.capture()
        assert result is None

    def test_record_returns_none(self):
        camera = MockCamera()
        result = camera.record("/tmp/test.mp4")
        assert result is None

    def test_is_available_returns_true(self):
        camera = MockCamera()
        assert camera.is_available() is True


class TestUSBCameraCoverage:
    def test_capture_returns_none(self):
        camera = USBCamera()
        result = camera.capture()
        assert result is None

    def test_record_returns_none(self):
        camera = USBCamera()
        result = camera.record("/tmp/test.mp4")
        assert result is None

    def test_is_available_returns_false(self):
        camera = USBCamera()
        assert camera.is_available() is False


class TestCameraFactoryCoverage:
    def test_create_usb_camera(self):
        factory = CameraFactory()
        camera = factory.create("usb")
        assert isinstance(camera, USBCamera)

    def test_create_unknown_raises_value_error(self):
        factory = CameraFactory()
        with pytest.raises(ValueError):
            factory.create("unknown_type")
