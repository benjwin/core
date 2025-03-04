"""The Nettigo Air Monitor coordinator."""

import asyncio
import logging
from typing import cast

from aiohttp.client_exceptions import ClientConnectorError
from nettigo_air_monitor import (
    ApiError,
    InvalidSensorDataError,
    NAMSensors,
    NettigoAirMonitor,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class NAMDataUpdateCoordinator(DataUpdateCoordinator[NAMSensors]):
    """Class to manage fetching Nettigo Air Monitor data."""

    def __init__(
        self,
        hass: HomeAssistant,
        nam: NettigoAirMonitor,
        unique_id: str | None,
    ) -> None:
        """Initialize."""
        self._unique_id = unique_id
        self.nam = nam

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL
        )

    async def _async_update_data(self) -> NAMSensors:
        """Update data via library."""
        try:
            async with asyncio.timeout(10):
                data = await self.nam.async_update()
        # We do not need to catch AuthFailed exception here because sensor data is
        # always available without authorization.
        except (ApiError, ClientConnectorError, InvalidSensorDataError) as error:
            raise UpdateFailed(error) from error

        return data

    @property
    def unique_id(self) -> str | None:
        """Return a unique_id."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, cast(str, self._unique_id))},
            name="Nettigo Air Monitor",
            sw_version=self.nam.software_version,
            manufacturer=MANUFACTURER,
            configuration_url=f"http://{self.nam.host}/",
        )
