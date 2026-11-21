from netmiko import ConnectHandler
x = 18
THUIS = True 
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
    "password": "pxl"
}

vlans = {
    int(f"1{x}"): f"172.16.{x}.2",
    int(f"2{x}"): f"172.16.{x}.66",
    int(f"3{x}"): f"172.16.{x}.130",
    int(f"4{x}"): f"172.16.{x}.194"
}

networks = { 
    int(f"1{x}"): f"172.16.{x}.0",
    int(f"2{x}"): f"172.16.{x}.64",
    int(f"3{x}"): f"172.16.{x}.128",
    int(f"4{x}"): f"172.16.{x}.192"
} #Voor OSPF nodig
commands = [f"hostname LAB-SR{x}-R01"]
for vlan, ip in vlans.items():
    if THUIS and vlan == int(f"1{x}"):
        continue  # VLAN 118 overslaan: zit al op GigabitEthernet1 (SSH)
    commands.extend([
        f"interface {inside_if}.{vlan}",
        f"encapsulation dot1Q {vlan}",
        f"ip address {ip} 255.255.255.192"
    ])

commands.extend([
    f"interface {inside_if}",
    "no shutdown",
    f"interface {inside_if}.99",
    "encapsulation dot1Q 99 native",
    f"interface {outside_if}",
    f"ip address 10.199.66.{200 + x} 255.255.255.224",
    "no shutdown"
])

#OSPF
commands.extend([
    "router ospf 10",
    f"router-id {x}.{x}.{x}.{x}",
    f"network 172.16.{x}.192 0.0.0.63 area 0",
    "network 10.199.66.192 0.0.0.31 area 0", #Outside route (gig1)
    "default-information originate"
])

#ACLS buiten <-> VLAN 218, 318, 418 toestaan, vlan 118 blokced OSPF altijd
commands.extend(["ip access-list extended OUTSIDE_IN", "permit ospf any any"])
for vlan, net in networks.items():
    actie = "deny" if vlan == int(f"1{x}") else "permit"
    commands.append(f"{actie} ip any {net} 0.0.0.63")

#Buiten naar binnen
commands.extend(["ip access-list extended INSIDE_OUT", "permit ospf any any"])
for vlan, net in networks.items():
    actie = "deny" if vlan == int(f"1{x}") else "permit"
    commands.append(f"{actie} ip {net} 0.0.0.63 any") #any vanachter => naar alles dus naar buiten
#ACLS buiteninterface zetten
commands.extend([
    f"interface {outside_if}",
    "ip access-group OUTSIDE_IN in",
    "ip access-group INSIDE_OUT out"
])

connection = ConnectHandler(**device)
output = connection.send_config_set(commands)
print(output)
#print(connection.save_config())
connection.disconnect()