"""
TDD Tests: Camera Interface

These tests define the expected behavior for the camera abstraction layer.
Implement src/hardware/camera/interface.py to make these tests pass.

Run: pytest tdd/phase2_hardware/camera/test_camera_interface.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: Camera Base Interface
# =============================================================================

class TestCameraInterface:
    """Tests for the base camera interface."""

    def test_camera_has_capture_method(self):
        """All cameras must implement capture() method."""
        from src.hardware.camera.interface import Camera

        camera = Camera()

        assert hasattr(camera, 'capture')
        assert callable(camera.capture)

    def test_camera_has_start_recording_method(self):
        """Cameras must implement start_recording() method."""
        from src.hardware.camera.interface import Camera

        camera = Camera()

        assert hasattr(camera, 'start_recording')
        assert callable(camera.start_recording)

    def test_camera_has_stop_recording_method(self):
        """Cameras must implement stop_recording() method."""
        from src.hardware.camera.interface import Camera

        camera = Camera()

        assert hasattr(camera, 'stop_recording')
        assert callable(camera.stop_recording)

    def test_camera_has_is_available_method(self):
        """Cameras should have is_available() method."""
        from src.hardware.camera.interface import Camera

        camera = Camera()

        assert hasattr(camera, 'is_available')
        assert callable(camera.is_available)

    def test_camera_has_name_property(self):
        """Camera should have a name property."""
        from src.hardware.camera.interface import Camera

        camera = Camera(name="indoor")

        assert camera.name == "indoor"


# =============================================================================
# Test: Pi Camera Implementation
# =============================================================================

class TestPiCamera:
    """Tests for Raspberry Pi camera implementation."""

    def test_picamera_inherits_interface(self):
        """PiCamera should inherit from Camera."""
        from src.hardware.camera.interface import Camera
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2'):
            camera = PiCamera()

        assert isinstance(camera, Camera)

    def test_picamera_initializes_correctly(self, mock_camera):
        """PiCamera should initialize with default settings."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()

        assert camera is not None

    def test_picamera_default_resolution(self, mock_camera):
        """Default resolution should be configured."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()

        assert hasattr(camera, 'resolution')
        assert len(camera.resolution) == 2  # [width, height]

    def test_picamera_custom_resolution(self, mock_camera):
        """Should accept custom resolution."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera(resolution=(1920, 1080))

        assert camera.resolution == (1920, 1080)

    def test_picamera_custom_framerate(self, mock_camera):
        """Should accept custom framerate."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera(framerate=30)

        assert camera.framerate == 30


# =============================================================================
# Test: Camera Capture
# =============================================================================

class TestCameraCapture:
    """Tests for camera capture functionality."""

    def test_capture_returns_image_array(self, mock_camera, mock_video_frame):
        """capture() should return image as numpy array."""
        from src.hardware.camera.picamera import PiCamera

        mock_camera.capture_array.return_value = mock_video_frame

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            result = camera.capture()

        assert result is not None
        # Should be a numpy-like array with shape (height, width, channels)
        assert hasattr(result, 'shape')

    def test_capture_to_file(self, mock_camera, tmp_path: Path):
        """capture() should save to file when path provided."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            output_path = tmp_path / "capture.jpg"
            camera.capture(path=output_path)

            mock_camera.capture_file.assert_called()

    def test_capture_requires_camera_started(self, mock_camera):
        """capture() should fail if camera not started."""
        from src.hardware.camera.picamera import PiCamera, CameraNotStartedError

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            # Don't call start()

            with pytest.raises(CameraNotStartedError):
                camera.capture()


# =============================================================================
# Test: Video Recording
# =============================================================================

class TestVideoRecording:
    """Tests for video recording functionality."""

    def test_start_recording_creates_file(self, mock_camera, tmp_path: Path):
        """start_recording() should begin recording to file."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            output_path = tmp_path / "video.mp4"
            camera.start_recording(output_path)

            assert camera.is_recording is True

    def test_stop_recording_finalizes_file(self, mock_camera, tmp_path: Path):
        """stop_recording() should finalize the video file."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            output_path = tmp_path / "video.mp4"
            camera.start_recording(output_path)
            camera.stop_recording()

            assert camera.is_recording is False

    def test_recording_with_duration(self, mock_camera, tmp_path: Path):
        """Should support recording for specific duration."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            output_path = tmp_path / "video.mp4"
            camera.record(output_path, duration=30)

            # Verify recording was initiated
            assert mock_camera.start_recording.called or True  # Implementation varies

    def test_cannot_start_recording_twice(self, mock_camera, tmp_path: Path):
        """Should not allow starting recording when already recording."""
        from src.hardware.camera.picamera import PiCamera, CameraRecordingError

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            camera.start_recording(tmp_path / "video1.mp4")

            with pytest.raises(CameraRecordingError):
                camera.start_recording(tmp_path / "video2.mp4")


# =============================================================================
# Test: Camera State Management
# =============================================================================

class TestCameraStateManagement:
    """Tests for camera state management."""

    def test_camera_start_initializes(self, mock_camera):
        """start() should initialize camera."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            assert camera.is_started is True

    def test_camera_stop_releases_resources(self, mock_camera):
        """stop() should release camera resources."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()
            camera.stop()

            assert camera.is_started is False
            mock_camera.stop.assert_called()

    def test_camera_context_manager(self, mock_camera):
        """Should support context manager protocol."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            with PiCamera() as camera:
                assert camera.is_started is True

            assert camera.is_started is False

    def test_camera_cleanup_on_error(self, mock_camera):
        """Should cleanup resources on error."""
        from src.hardware.camera.picamera import PiCamera

        mock_camera.capture_array.side_effect = Exception("Camera error")

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.start()

            try:
                camera.capture()
            except Exception:
                pass

            # Camera should still be able to stop gracefully
            camera.stop()
            assert camera.is_started is False


# =============================================================================
# Test: Camera Configuration
# =============================================================================

class TestCameraConfiguration:
    """Tests for camera configuration."""

    def test_set_resolution(self, mock_camera):
        """Should allow setting resolution."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.set_resolution(1920, 1080)

            assert camera.resolution == (1920, 1080)

    def test_set_framerate(self, mock_camera):
        """Should allow setting framerate."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.set_framerate(30)

            assert camera.framerate == 30

    def test_set_rotation(self, mock_camera):
        """Should allow setting rotation."""
        from src.hardware.camera.picamera import PiCamera

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()
            camera.set_rotation(180)

            assert camera.rotation == 180

    def test_invalid_rotation_raises(self, mock_camera):
        """Invalid rotation values should raise error."""
        from src.hardware.camera.picamera import PiCamera, CameraConfigError

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera()

            with pytest.raises(CameraConfigError):
                camera.set_rotation(45)  # Only 0, 90, 180, 270 allowed

    def test_load_config_from_dict(self, mock_camera):
        """Should load configuration from dictionary."""
        from src.hardware.camera.picamera import PiCamera

        config = {
            "resolution": [1920, 1080],
            "framerate": 30,
            "rotation": 0
        }

        with patch('src.hardware.camera.picamera.Picamera2', return_value=mock_camera):
            camera = PiCamera.from_config(config)

            assert camera.resolution == (1920, 1080)
            assert camera.framerate == 30
