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

import enum
from typing import Tuple, List, Callable, Dict
from .c_binding import call_vimba_c, byref, sizeof, decode_cstr
from .c_binding import VmbInterface, VmbInterfaceInfo, VmbHandle, VmbUint32
from .feature import discover_features, FeatureTypes, FeaturesTuple
from .shared import filter_features_by_name, filter_features_by_type, filter_affected_features, \
                    filter_selected_features, filter_features_by_category, \
                    read_memory_impl, write_memory_impl, read_registers_impl, write_registers_impl
from .util import TraceEnable, RuntimeTypeCheckEnable


__all__ = [
    'InterfaceType',
    'Interface',
    'InterfaceEvent',
    'InterfaceChangeHandler',
    'InterfacesTuple',
    'InterfacesList',
    'discover_interfaces',
    'discover_interface'
]


# Forward declarations
InterfaceChangeHandler = Callable[['Interface', 'InterfaceEvent'], None]
InterfacesTuple = Tuple['Interface', ...]
InterfacesList = List['Interface']


class InterfaceType(enum.IntEnum):
    """Enum specifying all interface types.

    Enum values:
        Unknown  - Interface is not known to this VimbaPython version.
        Firewire - 1394
        Ethernet - Gigabit Ethernet
        Usb      - USB 3.0
        CL       - Camera Link
        CSI2     - CSI-2
    """
    Unknown = VmbInterface.Unknown
    Firewire = VmbInterface.Firewire
    Ethernet = VmbInterface.Ethernet
    Usb = VmbInterface.Usb
    CL = VmbInterface.CL
    CSI2 = VmbInterface.CSI2


class InterfaceEvent(enum.IntEnum):
    """Enum specifying a Interface Event

    Enum values:
        Missing     - A known Interface disappeared from the bus
        Detected    - A new Interface was discovered
        Reachable   - A known Interface can be accessed
        Unreachable - A known Interface cannot be accessed anymore
    """
    Missing = 0
    Detected = 1
    Reachable = 2
    Unreachable = 3


class Interface:
    """This class allows access a Interface detected by the Vimba System.
    Camera is meant be used in conjunction with the "with" - Statement. On entering a context
    all Interface features are detected and can be accessed within the context. Basic Interface
    properties like Name can be access outside of the context.
    """

    @TraceEnable()
    def __init__(self, info: VmbInterfaceInfo):
        """Do not call directly. Access Interfaces via vimba.System instead."""
        self.__handle: VmbHandle = VmbHandle(0)
        self.__info: VmbInterfaceInfo = info
        self.__feats: FeaturesTuple = ()
        self.__context_cnt: int = 0

    @TraceEnable()
    def __enter__(self):
        if not self.__context_cnt:
            self._open()

        self.__context_cnt += 1
        return self

    @TraceEnable()
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__context_cnt -= 1

        if not self.__context_cnt:
            self._close()

    def __str__(self):
        return 'Interface(id={})'.format(self.get_id())

    def __repr__(self):
        rep = 'Interface'
        rep += '(__handle=' + repr(self.__handle)
        rep += ',__info=' + repr(self.__info)
        rep += ')'
        return rep

    def get_id(self) -> str:
        """Get Interface Id, e.g. VimbaUSBInterface_0x0."""
        return decode_cstr(self.__info.interfaceIdString)

    def get_type(self) -> InterfaceType:
        """Get Interface Type, e.g. InterfaceType.Usb."""
        return InterfaceType(self.__info.interfaceType)

    def get_name(self) -> str:
        """Get Interface Name, e.g. Vimba USB Interface."""
        return decode_cstr(self.__info.interfaceName)

    def get_serial(self) -> str:
        """Get Interface Serial or '' if not set."""
        return decode_cstr(self.__info.serialString)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def read_memory(self, addr: int, max_bytes: int) -> bytes:
        """Read a byte sequence from a given memory address.

        Arguments:
            addr: Starting address to read from.
            max_bytes: Maximum number of bytes to read from addr.

        Returns:
            Read memory contents as bytes.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if addr is negative
            ValueError if max_bytes is negative.
            ValueError if the memory access was invalid.
        """
        return read_memory_impl(self.__handle, addr, max_bytes)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def write_memory(self, addr: int, data: bytes):
        """ Write a byte sequence to a given memory address.

        Arguments:
            addr: Address to write the content of 'data' too.
            data: Byte sequence to write at address 'addr'.

        Raises:
            TypeError if parameters do not match their type hint.
            ValueError if addr is negative.
        """
        return write_memory_impl(self.__handle, addr, data)

    @TraceEnable()
    def read_registers(self, addrs: Tuple[int, ...]) -> Dict[int, int]:
        """Read contents of multiple registers.

        Arguments:
            addrs: Sequence of addresses that should be read iteratively.

        Return:
            Dictionary containing a mapping from given address to the read register values.

        Raises:
            ValueError if any address in addrs is negative.
            ValueError if the register access was invalid.
        """
        return read_registers_impl(self.__handle, addrs)

    @TraceEnable()
    def write_registers(self, addrs_values: Dict[int, int]):
        """Write data to multiple Registers.

        Arguments:
            addrs_values: Mapping between Register addresses and the data to write.

        Raises:
            ValueError if any address in addrs_values is negative.
            ValueError if the register access was invalid.
        """
        return write_registers_impl(self.__handle, addrs_values)

    def get_all_features(self) -> FeaturesTuple:
        """Get access to all discovered features of this Interface:

        Returns:
            A set of all currently detected features. Returns an empty set then called
            outside of 'with' - statement.
        """
        return self.__feats

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_features_affected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features affected by a specific interface feature.

        Arguments:
            feat - Feature used find features that are affected by 'feat'.

        Returns:
            A set of features affected by changes on 'feat'. Can be an empty set if 'feat'
            does not affect any features.

        Raises:
            TypeError if parameters do not match their type hint.
            VimbaFeatureError if 'feat' is not a feature of this interface.
        """
        return filter_affected_features(self.__feats, feat)

    @TraceEnable()
    @RuntimeTypeCheckEnable()
    def get_features_selected_by(self, feat: FeatureTypes) -> FeaturesTuple:
        """Get all features selected by a specific interface feature.

        Arguments:
            feat - Feature used find features that are selected by 'feat'.

        Returns:
            A set of features selected by changes on 'feat'. Can be an empty set if 'feat'
            does not affect any features.

        Raises:
            TypeError if 'feat' is not of any feature type.
            VimbaFeatureError if 'feat' is not a feature of this interface.
        """
        return filter_selected_features(self.__feats, feat)

    @RuntimeTypeCheckEnable()
    def get_features_by_type(self, feat_type: FeatureTypes) -> FeaturesTuple:
        """Get all interface features of a specific feature type.

        Valid FeatureTypes are: IntFeature, FloatFeature, StringFeature, BoolFeature,
        EnumFeature, CommandFeature, RawFeature

        Arguments:
            feat_type - FeatureType used find features of that type.

        Returns:
            A set of features of type 'feat_type'. Can be an empty set if there is
            no interface feature with the given type available.

        Raises:
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_type(self.__feats, feat_type)

    @RuntimeTypeCheckEnable()
    def get_features_by_category(self, category: str) -> FeaturesTuple:
        """Get all interface features of a specific category.

        Arguments:
            category - Category that should be used for filtering.

        Returns:
            A set of features of category 'category'. Can be an empty set if there is
            no interface feature of that category.

        Raises:
            TypeError if parameters do not match their type hint.
        """
        return filter_features_by_category(self.__feats, category)

    @RuntimeTypeCheckEnable()
    def get_feature_by_name(self, feat_name: str) -> FeatureTypes:
        """Get a interface feature by its name.

        Arguments:
            feat_name - Name used to find a feature.

        Returns:
            Feature with the associated name.

        Raises:
            TypeError if parameters do not match their type hint.
            VimbaFeatureError if no feature is associated with 'feat_name'.
        """
        return filter_features_by_name(self.__feats, feat_name)

    @TraceEnable()
    def _open(self):
        call_vimba_c('VmbInterfaceOpen', self.__info.interfaceIdString, byref(self.__handle))

        self.__feats = discover_features(self.__handle)

    @TraceEnable()
    def _close(self):
        for feat in self.__feats:
            feat.unregister_all_change_handlers()

        self.__feats = ()

        call_vimba_c('VmbInterfaceClose', self.__handle)

        self.__handle = VmbHandle(0)


@TraceEnable()
def discover_interfaces() -> InterfacesList:
    """Do not call directly. Access Interfaces via vimba.System instead."""

    result = []
    inters_count = VmbUint32(0)

    call_vimba_c('VmbInterfacesList', None, 0, byref(inters_count), sizeof(VmbInterfaceInfo))

    if inters_count:
        inters_found = VmbUint32(0)
        inters_infos = (VmbInterfaceInfo * inters_count.value)()

        call_vimba_c('VmbInterfacesList', inters_infos, inters_count, byref(inters_found),
                     sizeof(VmbInterfaceInfo))

        for info in inters_infos[:inters_found.value]:
            result.append(Interface(info))

    return result


@TraceEnable()
def discover_interface(id_: str) -> Interface:
    """Do not call directly. Access Interfaces via vimba.System instead."""

    # Since there is no function to query a single interface, discover all interfaces and
    # extract the Interface with the matching ID.
    inters = discover_interfaces()
    return [i for i in inters if id_ == i.get_id()].pop()
