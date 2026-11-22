from ncclient import manager
from getpass import getpass
import xml.dom.minidom

HOST = "172.16.18.2"
USER = "student"
PASSWORD = getpass("Wachtwoord: ")


def connect():
    return manager.connect(
        host=HOST, port=830, username=USER, password=PASSWORD,
        hostkey_verify=False, allow_agent=False, look_for_keys=False,
        device_params={"name": "iosxe"}, timeout=30,
    )


def pretty(reply):
    print(xml.dom.minidom.parseString(reply.xml).toprettyxml(indent="  "))

FILTER_IF = """
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name/>
    <description/>
    <enabled/>
  </interface>
</interfaces>
"""
FILTER_STATE = """
<interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name/>
    <oper-status/>
  </interface>
</interfaces-state>
"""

with connect() as m:
    print("===== get_config =====")
    pretty(m.get_config(source="running", filter=("subtree", FILTER_STATE)))
    print("===== get =====")
    pretty(m.get(filter=("subtree", FILTER_STATE)))