import unittest
from netmiko import ConnectHandler

x = 18
outside_if = "GigabitEthernet0/0/1"   # thuis: GigabitEthernet3

device = {
    "device_type": "cisco_ios",
    "host": f"172.16.{x}.2",
    "username": "student",
    "password": "pxl",
}

class TestR1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with ConnectHandler(**device) as conn:
            cls.prompt = conn.find_prompt()
            cls.int_brief = conn.send_command("show ip interface brief")
            cls.ospf = conn.send_command("show ip protocols")
            cls.route = conn.send_command("show ip route")
            cls.acl = conn.send_command("show access-lists")
            cls.outside = conn.send_command(f"show ip interface {outside_if}")

    # a. Hostname
    def test_a_hostname(self):
        self.assertIn(f"LAB-SR{x}-R01", self.prompt)

    # b. Interfaces: adres + status
    def test_b_interfaces(self):
        verwacht = [f"172.16.{x}.66", f"172.16.{x}.130", f"172.16.{x}.194", f"10.199.66.{200 + x}"]
        for ip in verwacht:
            with self.subTest(ip=ip):
                regel = [l for l in self.int_brief.splitlines() if ip in l]
                self.assertTrue(regel, f"{ip} niet gevonden")
                self.assertTrue(regel[0].endswith("up"), f"{ip} is niet up")

    # c. OSPF
    def test_c_ospf(self):
        self.assertIn('"ospf 10"', self.ospf)
        self.assertIn(f"{x}.{x}.{x}.{x}", self.ospf)
        self.assertIn(f"172.16.{x}.192 0.0.0.63 area 0", self.ospf)

    # d. Routing
    def test_d_routing(self):
        self.assertIn("0.0.0.0/0", self.route)          # default route
        self.assertIn(f"172.16.{x}.192/26", self.route)

    # e. Beveiliging
    def test_e_acl(self):
        self.assertIn("OUTSIDE_IN", self.acl)
        self.assertIn(f"deny ip any 172.16.{x}.0 0.0.0.63", self.acl)
        self.assertIn("OUTSIDE_IN", self.outside)       # ACL staat op de interface

if __name__ == "__main__":
    unittest.main(verbosity=2)