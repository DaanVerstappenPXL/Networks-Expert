"""
LAB 3 - Deel 5: Automated Testing van R1 met unittest + Netmiko

Uitvoeren:  python3 R1_config_test.py
"""
import re
import unittest
from netmiko import ConnectHandler

# ------------------------------------------------------------------
# Instellingen
# ------------------------------------------------------------------
x = 18
THUIS = True   # True = virtuele router thuis, False = echte router in het labo

if THUIS:
    inside_if = "GigabitEthernet2"
    outside_if = "GigabitEthernet3"
else:
    inside_if = "GigabitEthernet0/0/0"
    outside_if = "GigabitEthernet0/0/1"

device = {
    "device_type": "cisco_ios",
    "host": f"172.16.{x}.2",
    "username": "student",
    "password": "pxl",
}

HOSTNAME = f"LAB-SR{x}-R01"
ROUTER_ID = f"{x}.{x}.{x}.{x}"
OUTSIDE_IP = f"10.199.66.{200 + x}"

# VLAN -> (IP van de router, netwerkadres)
VLANS = {
    int(f"1{x}"): (f"172.16.{x}.2",   f"172.16.{x}.0"),
    int(f"2{x}"): (f"172.16.{x}.66",  f"172.16.{x}.64"),
    int(f"3{x}"): (f"172.16.{x}.130", f"172.16.{x}.128"),
    int(f"4{x}"): (f"172.16.{x}.194", f"172.16.{x}.192"),
}
VLAN_1X = int(f"1{x}")

# Welke interfaces verwachten we, met welk IP?
VERWACHTE_INTERFACES = {}
for vlan, (ip, net) in VLANS.items():
    if THUIS and vlan == VLAN_1X:
        VERWACHTE_INTERFACES["GigabitEthernet1"] = ip   # thuis = beheer op G1
    else:
        VERWACHTE_INTERFACES[f"{inside_if}.{vlan}"] = ip
VERWACHTE_INTERFACES[outside_if] = OUTSIDE_IP

# ------------------------------------------------------------------
# Gegevens EEN keer ophalen bij de router (sneller dan per test)
# ------------------------------------------------------------------
OUT = {}


def setUpModule():
    with ConnectHandler(**device) as conn:
        OUT["prompt"] = conn.find_prompt()
        OUT["int_brief"] = conn.send_command("show ip interface brief")
        OUT["ospf"] = conn.send_command("show ip ospf")
        OUT["ospf_cfg"] = conn.send_command("show running-config | section router ospf")
        OUT["protocols"] = conn.send_command("show ip protocols")
        OUT["neighbors"] = conn.send_command("show ip ospf neighbor")
        OUT["route"] = conn.send_command("show ip route")
        OUT["acl"] = conn.send_command("show access-lists")
        OUT["outside"] = conn.send_command(f"show ip interface {outside_if}")
        OUT["ssh"] = conn.send_command("show ip ssh")
        OUT["vty"] = conn.send_command("show running-config | section line vty")
    OUT["interfaces"] = parse_int_brief(OUT["int_brief"])


def parse_int_brief(output):
    """Maakt van 'show ip interface brief' een dict:
    {naam: {"ip": ..., "status": ..., "protocol": ...}}"""
    interfaces = {}
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        interfaces[parts[0]] = {
            "ip": parts[1],
            "status": " ".join(parts[4:-1]),   # "up", "down" of "administratively down"
            "protocol": parts[-1],
        }
    return interfaces


def label(tekst):
    """Decorator: geeft een test de tekst die in de uitvoer verschijnt."""
    def deco(func):
        func.__doc__ = tekst
        return func
    return deco


class Basis(unittest.TestCase):
    longMessage = False   # toon alleen onze eigen, korte foutmelding


def kort(naam):
    """GigabitEthernet0/0/0.218 -> G0/0/0.218"""
    return naam.replace("GigabitEthernet", "G")


# ------------------------------------------------------------------
# a. Hostname
# ------------------------------------------------------------------
class A_Hostname(Basis):
    groep = "Hostname"

    @label("{}".format(HOSTNAME))
    def test_hostname(self):
        self.assertEqual(OUT["prompt"].rstrip("#>"), HOSTNAME, f"hostname is {OUT['prompt']}")


# ------------------------------------------------------------------
# b. Interfaces: adressering + status (tests worden automatisch gemaakt)
# ------------------------------------------------------------------
class B_Interfaces(Basis):
    groep = "Interfaces"


def maak_interface_test(naam, ip):
    def test(self):
        intf = OUT["interfaces"].get(naam)
        self.assertIsNotNone(intf, f"{naam} bestaat niet")
        self.assertEqual(intf["ip"], ip, f"IP is {intf['ip']}, verwacht {ip}")
        self.assertEqual(intf["status"], "up", f"status is {intf['status']}")
        self.assertEqual(intf["protocol"], "up", f"protocol is {intf['protocol']}")
    test.__doc__ = f"{kort(naam)} {ip} up/up"
    return test


for i, (naam, ip) in enumerate(VERWACHTE_INTERFACES.items()):
    setattr(B_Interfaces, f"test_{i:02d}", maak_interface_test(naam, ip))


# ------------------------------------------------------------------
# c. OSPF
# ------------------------------------------------------------------
class C_OSPF(Basis):
    groep = "OSPF"

    @label("Process 10, router-id {}".format(ROUTER_ID))
    def test_1_process_en_router_id(self):
        self.assertRegex(OUT["ospf"], rf'Routing Process "ospf 10" with ID {re.escape(ROUTER_ID)}',
                         "process 10 of router-id niet gevonden")

    @label("Network VLAN 4{} in area 0".format(x))
    def test_2_network_vlan4x(self):
        self.assertRegex(OUT["protocols"], rf"172\.16\.{x}\.192 0\.0\.0\.63 area 0", "network-regel ontbreekt")

    def test_3_network_outside(self):
        """Network outside in area 0"""
        self.assertRegex(OUT["protocols"], r"10\.199\.66\.192 0\.0\.0\.31 area 0", "network-regel ontbreekt")

    def test_4_default_information(self):
        """Default route wordt gedeeld"""
        self.assertIn("default-information originate", OUT["ospf_cfg"], "default-information originate ontbreekt")

    def test_5_neighbor(self):
        """OSPF neighbor FULL"""
        self.assertIn("FULL", OUT["neighbors"], "geen OSPF-buur in FULL-status")


# ------------------------------------------------------------------
# d. Routing
# ------------------------------------------------------------------
class D_Routing(Basis):
    groep = "Routing"

    def test_1_default_route(self):
        """Default route 0.0.0.0/0 aanwezig"""
        self.assertIn("0.0.0.0/0", OUT["route"], "geen default route in de routingtabel")

    def test_2_connected_netwerken(self):
        """Alle VLAN-netwerken connected"""
        for vlan, (ip, net) in VLANS.items():
            with self.subTest(vlan=vlan):
                self.assertRegex(OUT["route"], rf"C\s+{re.escape(net)}/26", f"VLAN {vlan} niet connected")

    def test_3_outside_connected(self):
        """Outside netwerk connected"""
        self.assertRegex(OUT["route"], r"C\s+10\.199\.66\.192/27", "10.199.66.192/27 niet connected")


# ------------------------------------------------------------------
# e. Beveiliging
# ------------------------------------------------------------------
class E_Beveiliging(Basis):
    groep = "Beveiliging"

    def test_1_acls_bestaan(self):
        """ACL OUTSIDE_IN en INSIDE_OUT bestaan"""
        self.assertIn("Extended IP access list OUTSIDE_IN", OUT["acl"], "OUTSIDE_IN ontbreekt")
        self.assertIn("Extended IP access list INSIDE_OUT", OUT["acl"], "INSIDE_OUT ontbreekt")

    @label("VLAN 1{} geblokkeerd (in en uit)".format(x))
    def test_2_vlan1x_geblokkeerd(self):
        net = re.escape(f"172.16.{x}.0")
        self.assertRegex(OUT["acl"], rf"deny ip any {net} 0\.0\.0\.63", "deny in OUTSIDE_IN ontbreekt")
        self.assertRegex(OUT["acl"], rf"deny ip {net} 0\.0\.0\.63 any", "deny in INSIDE_OUT ontbreekt")

    @label("VLAN 2{0}, 3{0}, 4{0} toegelaten".format(x))
    def test_3_andere_vlans_toegelaten(self):
        for vlan, (ip, net) in VLANS.items():
            if vlan == VLAN_1X:
                continue
            with self.subTest(vlan=vlan):
                self.assertRegex(OUT["acl"], rf"permit ip any {re.escape(net)} 0\.0\.0\.63", "permit ontbreekt")

    def test_4_ospf_toegelaten(self):
        """OSPF altijd toegelaten"""
        self.assertIn("permit ospf any any", OUT["acl"], "permit ospf ontbreekt")

    @label("ACL's op {} (in + out)".format(kort(outside_if)))
    def test_5_acl_op_outside(self):
        self.assertRegex(OUT["outside"], r"Inbound\s+access list is OUTSIDE_IN", "OUTSIDE_IN niet inbound")
        self.assertRegex(OUT["outside"], r"Outgoing access list is INSIDE_OUT", "INSIDE_OUT niet outbound")

    def test_6_ssh(self):
        """SSH ingeschakeld, alleen SSH op vty"""
        self.assertIn("SSH Enabled", OUT["ssh"], "SSH staat niet aan")
        self.assertIn("transport input ssh", OUT["vty"], "vty laat niet alleen SSH toe")


# ------------------------------------------------------------------
# Mooie uitvoer:  naam ....... [PASS] / [FAIL]
# ------------------------------------------------------------------
class MooiResultaat(unittest.TestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.huidige_groep = None
        self.gefaald = set()

    def startTest(self, test):
        super().startTest(test)
        groep = getattr(test, "groep", "")
        if groep != self.huidige_groep:
            print(f"\n{groep}:")
            self.huidige_groep = groep

    def regel(self, test, status, reden=""):
        label = test.shortDescription() or getattr(test, "_testMethodName", str(test))
        print(f"    {label:<42}[{status}]")
        if reden:
            print(f"        -> {reden}")

    def addSuccess(self, test):
        super().addSuccess(test)
        self.regel(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.gefaald.add(test.id())
        self.regel(test, "FAIL", str(err[1]).splitlines()[0])

    def addError(self, test, err):
        super().addError(test, err)
        self.gefaald.add(test.id())
        self.regel(test, "ERROR", str(err[1]).splitlines()[0])

    def addSubTest(self, test, subtest, err):
        # een mislukte subtest telt als FAIL voor de hele test
        if err is not None:
            super().addSubTest(test, subtest, err)
            self.gefaald.add(test.id())
            self.regel(test, "FAIL", f"{subtest._subDescription()}: {str(err[1]).splitlines()[0]}")


if __name__ == "__main__":
    print("===== R1 CONFIGURATION TEST =====")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for klasse in (A_Hostname, B_Interfaces, C_OSPF, D_Routing, E_Beveiliging):
        suite.addTests(loader.loadTestsFromTestCase(klasse))

    resultaat = MooiResultaat()
    suite.run(resultaat)

    totaal = resultaat.testsRun
    fout = len(resultaat.gefaald)
    print(f"\n===== {totaal - fout}/{totaal} tests geslaagd =====")