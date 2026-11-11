from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "172.16.18.2",
    "username": "student",
    "password": "pxl"
}

connection = ConnectHandler(**device)
run_cfg = connection.send_command("show running-config")
intf_brief = connection.send_command("show ip interface brief")
connection.disconnect()

print("===== R1 CONFIGURATION TEST (TAFEL 18) =====")
checks = {
    "Hostname LAB-SR18-R01": "hostname LAB-SR18-R01" in run_cfg,
    "G0/0/0.118 (172.16.18.2)": "172.16.18.2" in intf_brief,
    "G0/0/0.218 (172.16.18.66)": "172.16.18.66" in intf_brief,
    "G0/0/0.318 (172.16.18.130)": "172.16.18.130" in intf_brief,
    "G0/0/0.418 (172.16.18.194)": "172.16.18.194" in intf_brief,
    "G0/0/1 Outside (10.199.66.218)": "10.199.66.218" in intf_brief,
    "OSPF Process 18 configured": "router ospf 18" in run_cfg,
    "ACL OUTSIDE_IN & INSIDE_OUT": "ip access-list extended OUTSIDE_IN" in run_cfg and "ip access-list extended INSIDE_OUT" in run_cfg
}

for item, passed in checks.items():
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{item:<34} {status}")
