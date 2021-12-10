import asyncio, logging
from typing import Dict, Optional, List, Tuple

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from bless.exceptions import BlessUnsupportedHardware

from dbus_next.aio import MessageBus, ProxyObject, ProxyInterface
from dbus_next.introspection import Node

class BlueZGattAdapter:
    def __init__(self, bus: MessageBus):
        self.bus = bus

    async def find_adapter(self) -> Optional[str]:
        """
        Returns the first object that the bluez service has that has a Adapter1
        interface
        """
        bluez_obj: ProxyObject = self.bus.get_proxy_object(defs.BLUEZ_SERVICE, '/', Node.default())
        
        om: ProxyInterface = bluez_obj.get_interface(defs.OBJECT_MANAGER_INTERFACE)
        om_objects: Dict = await om.call_get_managed_objects()

        for o, props in om_objects.items():
            if defs.ADAPTER_INTERFACE in props.keys():
                return o
        return None


    async def get_adapter(self, adapter_path: Optional[str]) -> ProxyObject:
        """
        Gets the bluetooth adapter

        Returns
        -------
        ProxyObject
            The adapter object
        """
        if not adapter_path:
            adapter_path = await find_adapter(self.bus)

        intro = await self.bus.introspect(defs.BLUEZ_SERVICE, adapter_path)
        self.adapter = self.bus.get_proxy_object(defs.BLUEZ_SERVICE, adapter_path, intro)
        self.adapter_interface = self.adapter.get_interface(defs.ADAPTER_INTERFACE)
        return self.adapter


    async def ensure_power_on(self):
        """
        Check if adapter is powered on, try to power on otherwise
        """
        powered: bool = await self.adapter_interface.get_powered()
        logging.debug(f'Adapter powered = {powered}')
        if not powered:
            logging.info('Adapter not powered, trying to power on')
            await self.adapter_interface.set_powered(True)
    
    async def check_compat(self):
        """
        Check if peripheral role is available
        """
        roles: List[str] = await self.adapter_interface.get_roles()
        logging.debug(f'Adapter supported roles {roles}')
        if 'peripheral' not in roles:
            logging.error(f'Peripheral role not supported in {roles}')
            raise BlessUnsupportedHardware()

    async def get_address(self) -> Tuple[str, str]:
        """
        Returns
        -------
        Tuple[str, str]
            First the MAC address string, then the type: either 'public' or 'random'
        """
        addr: str = await self.adapter_interface.get_address()
        addr_type: str = await self.adapter_interface.get_address_type()
        return (addr, addr_type)