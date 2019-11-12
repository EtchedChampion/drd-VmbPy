import unittest
import threading
import os

from vimba import *
from vimba.frame import *


def dummy_frame_handler(cam: Camera, frame: Frame):
    pass


class RealCamTestsCameraTest(unittest.TestCase):
    def setUp(self):
        self.vimba = Vimba.get_instance()
        self.vimba._startup()

        self.cam = self.vimba.get_camera_by_id(self.get_test_camera_id())
        self.cam.set_access_mode(AccessMode.Full)
        self.cam.set_capture_timeout(2000)

    def tearDown(self):
        self.vimba._shutdown()

    def test_context_manager_access_mode(self):
        """Expectation: Entering Context must not throw in cases where the current access mode is
        within get_permitted_access_modes()
        """
        permitted_modes = self.cam.get_permitted_access_modes()

        # There are some known Issues regarding permissions from the underlaying C-Layer.
        # Filter buggy modes. This is a VimbaC issue not a VimbaPython issue
        permitted_modes = [p for p in permitted_modes if p not in (AccessMode.Lite,)]

        for mode in permitted_modes:
            self.cam.set_access_mode(mode)

            try:
                with self.cam:
                    pass

            except BaseException:
                self.fail()

    def test_context_manager_feature_discovery(self):
        """Expectation: Outside of context, all features must be cleared,
        inside of context all features must be detected.
        """

        self.assertEqual(self.cam.get_all_features(), ())

        with self.cam:
            self.assertNotEqual(self.cam.get_all_features(), ())

        self.assertEqual(self.cam.get_all_features(), ())

    def test_access_mode(self):
        """Expectation: set/get access mode"""
        self.cam.set_access_mode(AccessMode.None_)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.None_)
        self.cam.set_access_mode(AccessMode.Full)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.Full)
        self.cam.set_access_mode(AccessMode.Read)
        self.assertEqual(self.cam.get_access_mode(), AccessMode.Read)

    def test_set_get_capture_timeout(self):
        """Expectation: set/get capture timeout. Negative values lead to ValueError"""
        self.cam.set_capture_timeout(2001)
        self.assertEqual(self.cam.get_capture_timeout(), 2001)

        self.assertRaises(ValueError, self.cam.set_capture_timeout, 0)
        self.assertRaises(ValueError, self.cam.set_capture_timeout, -1)

        self.assertEqual(self.cam.get_capture_timeout(), 2001)

    def test_get_id(self):
        """Expectation: get decoded camera id"""
        self.assertTrue(self.cam.get_id())

    def test_get_name(self):
        """Expectation: get decoded camera name"""
        self.assertTrue(self.cam.get_name())

    def test_get_model(self):
        """Expectation: get decoded camera model"""
        self.assertTrue(self.cam.get_model())

    def test_get_serial(self):
        """Expectation: get decoded camera serial"""
        self.assertTrue(self.cam.get_serial())

    def test_get_permitted_access_modes(self):
        """Expectation: get currently permitted access modes"""
        expected = (AccessMode.Full, AccessMode.Read, AccessMode.Lite)
        self.assertEqual(self.cam.get_permitted_access_modes(), expected)

    def test_get_interface_id(self):
        """Expectation: get interface Id this camera is connected to"""
        self.assertTrue(self.cam.get_interface_id())

    def test_get_features_affected(self):
        """Expectation: Features that affect other features shall return a set of affected feature
        Features that don't affect other features shall return (). If a Feature is supplied that
        is not associated with that camera, a TypeError must be raised.
        """
        with self.cam:
            affect = self.cam.get_feature_by_name('Height')
            not_affect = self.cam.get_feature_by_name('AcquisitionFrameCount')

            self.assertEqual(self.cam.get_features_affected_by(not_affect), ())

            expected = (
                self.cam.get_feature_by_name('PayloadSize'),
            )

            feats = self.cam.get_features_affected_by(affect)

            for expected_feat in expected:
                self.assertIn(expected_feat, feats)

    def test_frame_iterator_limit_set(self):
        """Expectation: The Frame Iterator fetches the given number of images."""
        with self.cam:
            self.assertEqual(len([i for i in self.cam.get_frame_iter(0)]), 0)
            self.assertEqual(len([i for i in self.cam.get_frame_iter(1)]), 1)
            self.assertEqual(len([i for i in self.cam.get_frame_iter(7)]), 7)
            self.assertEqual(len([i for i in self.cam.get_frame_iter(11)]), 11)

    def test_frame_iterator_error(self):
        """Expectation: The Frame Iterator raises a VimbaCameraError on a
        negative limit and the camera raises an VimbaCameraError
        if the camera is not opened.
        """
        # Check limits
        self.assertRaises(ValueError, self.cam.get_frame_iter, -1)

        # Usage on closed camera
        try:
            [i for i in self.cam.get_frame_iter(1)]
            self.fail('Generator expression on closed camera must raise')

        except VimbaCameraError:
            pass

        # Iterator execution must throw if streaming is enabled
        with self.cam:
            self.cam.start_streaming(dummy_frame_handler, 5)

            self.assertRaises(VimbaCameraError, self.cam.get_frame)

            iter_ = self.cam.get_frame_iter(1)
            self.assertRaises(VimbaCameraError, iter_.__next__)

            # Stop Streaming: Everything should be fine.
            self.cam.stop_streaming()
            self.assertNoRaise(self.cam.get_frame)

            iter_ = self.cam.get_frame_iter(1)
            self.assertNoRaise(iter_.__next__)

    def test_get_frame(self):
        """Expectation: Gets single Frame without any exception. Image data must be set"""
        with self.cam:
            self.assertNoRaise(self.cam.get_frame)
            self.assertEqual(type(self.cam.get_frame()), Frame)

    def test_capture_error_outside_vimba_scope(self):
        """Expectation: Camera access outside of Vimba scope must lead to a VimbaCameraError"""
        frame_iter = None

        with self.cam:
            frame_iter = self.cam.get_frame_iter(1)

        # Shutdown API
        self.vimba._shutdown()

        # Access invalid Iterator
        self.assertRaises(VimbaCameraError, frame_iter.__next__)

    def test_capture_error_outside_camera_scope(self):
        """Expectation: Camera access outside of Camera scope must lead to a VimbaCameraError"""
        frame_iter = None

        with self.cam:
            frame_iter = self.cam.get_frame_iter(1)

        self.assertRaises(VimbaCameraError, frame_iter.__next__)

    def test_capture_timeout(self):
        """Expectation: Camera access outside of Camera scope must lead to a VimbaCameraError"""
        self.cam.set_capture_timeout(1)

        with self.cam:
            self.assertRaises(VimbaTimeout, self.cam.get_frame)

    def test_is_streaming(self):
        """Expectation: After start_streaming() is_streaming() must return true. After stop it must
        return false. If the camera context is left without stop_streaming(), leaving
        the context must stop streaming.
        """

        # Normal Operation
        self.assertEqual(self.cam.is_streaming(), False)
        with self.cam:
            self.cam.start_streaming(dummy_frame_handler)
            self.assertEqual(self.cam.is_streaming(), True)

            self.cam.stop_streaming()
            self.assertEqual(self.cam.is_streaming(), False)

        # Missing the stream stop. Close must stop streaming
        with self.cam:
            self.cam.start_streaming(dummy_frame_handler, 5)
            self.assertEqual(self.cam.is_streaming(), True)

        self.assertEqual(self.cam.is_streaming(), False)

    def test_streaming_error_frame_count(self):
        """Expectation: A negative or zero frame_count must lead to an value error"""
        self.assertRaises(ValueError, self.cam.start_streaming, dummy_frame_handler, 0)
        self.assertRaises(ValueError, self.cam.start_streaming, dummy_frame_handler, -1)

    def test_streaming(self):
        """Expectation: A given frame_handler must be executed for each buffered frame. """

        class FrameHandler:
            def __init__(self, frame_count, test):
                self.cnt = 0
                self.frame_count = frame_count
                self.test = test
                self.event = threading.Event()

            def __call__(self, cam: Camera, frame: Frame):
                self.test.assertEqual(self.cnt, frame.get_id())
                self.cnt += 1

                if self.cnt == self.frame_count:
                    self.event.set()

        timeout = 5.0
        frame_count = 10
        handler = FrameHandler(frame_count, self)

        with self.cam:
            self.cam.start_streaming(handler, frame_count)

            # Wait until the FrameHandler has been executed for each queued frame
            self.assertTrue(handler.event.wait(timeout))

            self.cam.stop_streaming()

    def test_streaming_queue(self):
        """Expectation: A given frame must be reused if it is enqueued again. """

        self.vimba.enable_log(LOG_CONFIG_INFO_FILE_ONLY)

        class FrameHandler:
            def __init__(self, frame_count, test):
                self.cnt = 0
                self.frame_count = frame_count
                self.test = test
                self.event = threading.Event()

            def __call__(self, cam: Camera, frame: Frame):
                self.test.assertEqual(self.cnt, frame.get_id())
                self.cnt += 1

                if self.cnt == self.frame_count:
                    self.event.set()

                cam.queue_frame(frame)

        timeout = 5.0
        frame_count = 5
        frame_reuse = 5
        handler = FrameHandler(frame_count * frame_reuse, self)

        with self.cam:
            self.cam.start_streaming(handler, frame_count)

            # Wait until the FrameHandler has been executed for each queued frame
            self.assertTrue(handler.event.wait(timeout))

            self.cam.stop_streaming()

        self.vimba.disable_log()

    def test_runtime_type_check(self):
        """Expectation: raise TypeError on passing invalid parameters"""
        self.assertRaises(TypeError, self.cam.set_access_mode, -1)
        self.assertRaises(TypeError, self.cam.set_capture_timeout, 'hi')
        self.assertRaises(TypeError, self.cam.get_features_affected_by, 'No Feature')
        self.assertRaises(TypeError, self.cam.get_features_selected_by, 'No Feature')
        self.assertRaises(TypeError, self.cam.get_features_by_type, 0.0)
        self.assertRaises(TypeError, self.cam.get_feature_by_name, 0)
        self.assertRaises(TypeError, self.cam.get_frame_iter, '3')

        def valid_handler(cam, frame):
            pass

        def invalid_handler_1(cam):
            pass

        def invalid_handler_2(cam, frame, extra):
            pass

        self.assertRaises(TypeError, self.cam.start_streaming, valid_handler, 'no int')
        self.assertRaises(TypeError, self.cam.start_streaming, invalid_handler_1)
        self.assertRaises(TypeError, self.cam.start_streaming, invalid_handler_2)
        self.assertRaises(TypeError, self.cam.save_settings, 0, PersistType.All)
        self.assertRaises(TypeError, self.cam.save_settings, 'foo.xml', 'false type')

    def test_save_load_settings(self):
        """Expectation: After settings export a settings change must be reverted by loading a
        Previously saved configuration.
        """

        file_name = 'test_save_load_settings.xml'

        with self.cam:
            feat_height = self.cam.get_feature_by_name('Height')
            old_val = feat_height.get()

            self.cam.save_settings(file_name, PersistType.All)

            min_, max_ = feat_height.get_range()
            inc = feat_height.get_increment()

            feat_height.set(max_ - min_ - inc)

            self.cam.load_settings(file_name, PersistType.All)
            os.remove(file_name)

            self.assertEqual(old_val, feat_height.get())

    def test_save_settings_verify_path(self):
        """Expectation: Valid files end with .xml and can be either a absolute path or relative
        path to the given File. Everything else is a ValueError.
        """
        valid_paths = (
            'valid1.xml',
            os.path.join('.', 'valid2.xml'),
            os.path.join('Test', 'valid3.xml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valid4.xml'),
        )

        with self.cam:
            self.assertRaises(ValueError, self.cam.save_settings, 'inval.xm', PersistType.All)

            for path in valid_paths:
                self.assertNoRaise(self.cam.save_settings, path, PersistType.All)
                os.remove(path)

    def test_load_settings_verify_path(self):
        """Expectation: Valid files end with .xml and must exist before before any execution. """
        valid_paths = (
            'valid1.xml',
            os.path.join('.', 'valid2.xml'),
            os.path.join('Test', 'valid3.xml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valid4.xml'),
        )

        with self.cam:
            self.assertRaises(ValueError, self.cam.load_settings, 'inval.xm', PersistType.All)

            for path in valid_paths:
                self.assertRaises(ValueError, self.cam.load_settings, path, PersistType.All)

            for path in valid_paths:
                self.cam.save_settings(path, PersistType.All)

                self.assertNoRaise(self.cam.load_settings, path, PersistType.All)
                os.remove(path)
