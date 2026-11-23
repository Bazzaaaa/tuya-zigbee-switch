"""The relay mode (decoupling) must fall back to normal button control on boot
and whenever the network is lost. The controller sets it again afterwards."""

from tests.conftest import Device, StubProc
from tests.zcl_consts import (
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_RELAY_MODE,
    ZCL_CLUSTER_ON_OFF_SWITCH_CONFIG,
    ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED,
    ZCL_ONOFF_CONFIGURATION_RELAY_MODE_SHORT,
)

HAL_ZIGBEE_NETWORK_NOT_JOINED = 0
HAL_ZIGBEE_NETWORK_JOINED = 1
HAL_ZIGBEE_NETWORK_JOINING = 2

# One momentary button (A0) and one relay (B0)
CONFIG = "A;B;SA0u;RB0;M;"
SWITCH_EP = 1
RELAY_EP = 2
BUTTON = "A0"
DEFAULT = str(ZCL_ONOFF_CONFIGURATION_RELAY_MODE_SHORT)
DETACHED = str(ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED)


def relay_mode(device: Device) -> str:
    return device.read_zigbee_attr(
        SWITCH_EP,
        ZCL_CLUSTER_ON_OFF_SWITCH_CONFIG,
        ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_RELAY_MODE,
    )


def test_default_relay_mode_on_fresh_boot() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        assert relay_mode(device) == DEFAULT
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "1"


def test_detached_mode_works_while_connected() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        assert relay_mode(device) == DETACHED
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "0"


def test_detached_mode_not_kept_after_reboot() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        assert relay_mode(device) == DETACHED

    # Reboot: NV is kept between sessions
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        assert relay_mode(device) == DEFAULT
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "1"


def test_detached_mode_cleared_when_network_lost() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "0"

        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)

        assert relay_mode(device) == DEFAULT
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "1"


def test_relay_mode_not_restored_on_reconnect_but_can_be_set_again() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)
        device.set_network(HAL_ZIGBEE_NETWORK_JOINED)
        # Firmware does not remember: the controller has to set it again
        assert relay_mode(device) == DEFAULT

        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        assert relay_mode(device) == DETACHED
        device.click_button(BUTTON)
        assert device.zcl_relay_get(RELAY_EP) == "0"


def test_detached_mode_cleared_while_joining() -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        device.zcl_switch_relay_mode_set(
            SWITCH_EP, ZCL_ONOFF_CONFIGURATION_RELAY_MODE_DETACHED
        )
        device.set_network(HAL_ZIGBEE_NETWORK_JOINING)
        assert relay_mode(device) == DEFAULT
