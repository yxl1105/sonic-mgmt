"""
Thrift SAI interface L3 tests
"""
import pytest
import socket
import sys
from struct import pack, unpack
import itertools
import logging
from sai_base_test import *

from switch import *

import debugpy
import pdb
logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.topology('t0')
]


def test_router_interface(ptfadapter, ports_list, cfg_facts, ptfhost, dut_ip):
    logger.info("Sending L2 packet port 1 -> port 2 [access vlan=10])")
    
    interface = ThriftInterface(dut_ip, ports_list)
    interface.setUp()
    switch_init(interface)

    pdb.set_trace()
    vlan_id = 10
    port1 = ports_list[0]
    port2 = ports_list[1]
    mac1 = '00:11:11:11:11:11'
    mac2 = '00:22:22:22:22:22'
    mac_action = SAI_PACKET_ACTION_FORWARD

    vlan_oid = sai_thrift_create_vlan(interface.client, vlan_id)
    vlan_member1 = sai_thrift_create_vlan_member(interface.client, vlan_oid, port1['sai_port_id'], SAI_VLAN_TAGGING_MODE_UNTAGGED)
    vlan_member2 = sai_thrift_create_vlan_member(interface.client, vlan_oid, port2['sai_port_id'], SAI_VLAN_TAGGING_MODE_UNTAGGED)

    attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
    attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value)
    interface.client.sai_thrift_set_port_attribute(port1['sai_port_id'], attr)
    interface.client.sai_thrift_set_port_attribute(port2['sai_port_id'], attr)

    sai_thrift_create_fdb(interface.client, vlan_oid, mac1, port1['sai_port_id'], mac_action)
    sai_thrift_create_fdb(interface.client, vlan_oid, mac2, port2['sai_port_id'], mac_action)

    pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                            eth_src='00:11:11:11:11:11',
                            ip_dst='10.0.0.1',
                            ip_id=101,
                            ip_ttl=64)

    try:
        send_packet(ptfadapter, port1["port_index"][0], str(pkt))
        verify_packets(ptfadapter, pkt, [port2["port_index"][0]])
    finally:
        sai_thrift_delete_fdb(interface.client, vlan_oid, mac1, port1['sai_port_id'])
        sai_thrift_delete_fdb(interface.client, vlan_oid, mac2, port2['sai_port_id'])

        attr_value = sai_thrift_attribute_value_t(u16=1)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value)
        interface.client.sai_thrift_set_port_attribute(port1['sai_port_id'], attr)
        interface.client.sai_thrift_set_port_attribute(port2['sai_port_id'], attr)

        interface.client.sai_thrift_remove_vlan_member(vlan_member1)
        interface.client.sai_thrift_remove_vlan_member(vlan_member2)
        interface.client.sai_thrift_remove_vlan(vlan_oid)
        interface.tearDown()