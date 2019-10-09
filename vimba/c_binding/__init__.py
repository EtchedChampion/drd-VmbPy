"""Submodule encapsulating the VimbaC access.

(C) 2019 Allied Vision Technologies GmbH - All Rights Reserved

<Insert license here>
"""

# Suppress 'imported but unused' - Error from static style checker.
# flake8: noqa: F401

__all__ = [
    # Exports from vimba_common
    'VmbInt8',
    'VmbUint8',
    'VmbInt16',
    'VmbUint16',
    'VmbInt32',
    'VmbUint32',
    'VmbInt64',
    'VmbUint64',
    'VmbHandle',
    'VmbBool',
    'VmbUchar',
    'VmbDouble',
    'VmbError',
    'VimbaCError',
    'decode_cstr',
    'decode_flags',

    # Exports from vimba_c
    'VmbPixelFormat',
    'VmbInterface',
    'VmbAccessMode',
    'VmbFeatureData',
    'VmbFeaturePersist',
    'VmbFeatureVisibility',
    'VmbFeatureFlags',
    'VmbFrameStatus',
    'VmbFrameFlags',
    'VmbVersionInfo',
    'VmbInterfaceInfo',
    'VmbCameraInfo',
    'VmbFeatureInfo',
    'VmbFeatureEnumEntry',
    'VmbFrame',
    'VmbFeaturePersistSettings',
    'VmbInvalidationCallback',
    'VmbFrameCallback',
    'G_VIMBA_C_HANDLE',
    'EXPECTED_VIMBA_C_VERSION',
    'call_vimba_c_func',

    # Exports from vimba_image_tranform

    # Exports from ctypes
    'byref',
    'sizeof',
    'create_string_buffer'
]

from .vimba_common import VmbInt8, VmbUint8, VmbInt16, VmbUint16, VmbInt32, VmbUint32, \
                          VmbInt64, VmbUint64, VmbHandle, VmbBool, VmbUchar, VmbDouble, VmbError, \
                          VimbaCError, decode_cstr, decode_flags

from .vimba_c import VmbPixelFormat, VmbInterface, VmbAccessMode, VmbFeatureData, \
                   VmbFeaturePersist, VmbFeatureVisibility, VmbFeatureFlags, VmbFrameStatus, \
                   VmbFrameFlags, VmbVersionInfo, VmbInterfaceInfo, VmbCameraInfo, VmbFeatureInfo, \
                   VmbFeatureEnumEntry, VmbFrame, VmbFeaturePersistSettings, \
                   VmbInvalidationCallback, VmbFrameCallback, G_VIMBA_C_HANDLE, \
                   EXPECTED_VIMBA_C_VERSION, call_vimba_c_func

from ctypes import byref, sizeof, create_string_buffer
