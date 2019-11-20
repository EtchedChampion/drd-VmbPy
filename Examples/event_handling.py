"""BSD 2-Clause License

Copyright (c) 2019, Allied Vision Technologies GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

THE SOFTWARE IS PRELIMINARY AND STILL IN TESTING AND VERIFICATION PHASE AND
IS PROVIDED ON AN “AS IS” AND “AS AVAILABLE” BASIS AND IS BELIEVED TO CONTAIN DEFECTS.
A PRIMARY PURPOSE OF THIS EARLY ACCESS IS TO OBTAIN FEEDBACK ON PERFORMANCE AND
THE IDENTIFICATION OF DEFECT SOFTWARE, HARDWARE AND DOCUMENTATION.
"""

import sys
from typing import Optional
from vimba import *


def print_preamble():
    print('////////////////////////////////////////')
    print('/// Vimba API Event Handling Example ///')
    print('////////////////////////////////////////\n')


def print_usage():
    print('Usage: python event_handling.py [camera_id]\n')
    print('Parameters:   camera_id    ID of the camera to use (optional)')


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Optional[str]:
    args = sys.argv[1:]
    argc = len(args)

    if argc not in (0, 1):
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return args[0] if argc == 1 else None


def get_camera(cam_id: Optional[str]):
    with Vimba.get_instance() as vimba:
        # Lookup Camera if it was specified.
        if cam_id:
            try:
                cam = vimba.get_camera_by_id(cam_id)

            except VimbaCameraError:
                abort('Failed to access Camera {}. Abort.'.format(cam_id))

        # If no camera was specified, use first detected camera.
        else:
            cams = vimba.get_all_cameras()
            if not cams:
                abort('No Camera detected. Abort.'.format(cam_id))

            cam = cams[0]

        # This example works only with GigE Cameras. Verify that Camera is connected to an
        # Ethernet Interface.
        inter = vimba.get_interface_by_id(cam.get_interface_id())

        if inter.get_type() != InterfaceType.Ethernet:
            abort('Example supports only GigE Cameras. Abort.')

        return cam


def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            cmd_feat = cam.get_feature_by_name('GVSPAdjustPacketSize')

            try:
                cmd_feat.run()

                while not cmd_feat.is_done():
                    pass

            except VimbaFeatureError:
                abort('Failed to set Feature \'GVSPAdjustPacketSize\'. Abort.')

        except VimbaFeatureError:
            pass


def get_feature(cam: Camera, feature_name: str):
    with cam:
        try:
            return cam.get_feature_by_name(feature_name)

        except VimbaFeatureError:
            abort('Failed to access Feature {}'.format(feature_name))


def set_feature_value(feature, value):
    try:
        feature.set(value)

    except VimbaFeatureError:
        abort('Failed to set {} on Feature {}'.format(str(value), feature.get_name()))


def feature_changed_handler(feature):
    msg = 'Feature \'{}\' changed value to \'{}\''
    print(msg.format(str(feature.get_name()), str(feature.get())), flush=True)


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        with get_camera(cam_id) as cam:

            setup_camera(cam)

            # Disable all events notifications
            feat_event_select = get_feature(cam, 'EventSelector')
            feat_event_notify = get_feature(cam, 'EventNotification')

            for event in feat_event_select.get_available_entries():
                set_feature_value(feat_event_select, event)
                set_feature_value(feat_event_notify, 'Off')

            # Enable event notifications on 'AcquisitionStart'
            set_feature_value(get_feature(cam, 'EventSelector'), 'AcquisitionStart')
            set_feature_value(get_feature(cam, 'EventNotification'), 'On')

            # Register Callable on all Feature in the '/EventControl/EventData' - category
            feats = cam.get_features_by_category('/EventControl/EventData')

            for feat in feats:
                feat.register_change_handler(feature_changed_handler)

            # Acquire a single Frame to trigger events.
            cam.get_frame()


if __name__ == '__main__':
    main()
