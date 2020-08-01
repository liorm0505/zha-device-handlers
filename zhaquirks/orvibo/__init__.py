import asyncio
import logging
import math

from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl.clusters.measurement import (
    IlluminanceMeasurement,
)
from zigpy.zcl.clusters.security import IasZone

from .. import Bus, LocalDataCluster
from ..const import (
    CLUSTER_COMMAND,
    OFF,
    ON,
    ZONE_STATE,
)

_LOGGER = logging.getLogger(__name__)

ORVIBO = "ORVIBO"
BATTERY_SIZE = "battery_size"
ZONE_TYPE = 0x0001
MOTION_TYPE = 0x000D


class OrviboCustomDevice(CustomDevice):
    """Custom device representing orvibo devices."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.battery_bus = Bus()
        if not hasattr(self, BATTERY_SIZE):
            self.battery_size = 10
        super().__init__(*args, **kwargs)


class MotionCluster(LocalDataCluster, IasZone):
    """Motion cluster."""

    cluster_id = IasZone.cluster_id

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self._timer_handle = None
        self.endpoint.device.motion_bus.add_listener(self)
        super()._update_attribute(ZONE_TYPE, MOTION_TYPE)

    def motion_event(self):
        """Motion event."""
        super().listener_event(CLUSTER_COMMAND, None, ZONE_STATE, [ON])

        _LOGGER.debug("%s - Received motion event message", self.endpoint.device.ieee)

        if self._timer_handle:
            self._timer_handle.cancel()

        loop = asyncio.get_event_loop()
        self._timer_handle = loop.call_later(15, self._turn_off)

    def _turn_off(self):
        _LOGGER.debug("%s - Resetting motion sensor", self.endpoint.device.ieee)
        self._timer_handle = None
        super().listener_event(CLUSTER_COMMAND, None, ZONE_STATE, [OFF])

