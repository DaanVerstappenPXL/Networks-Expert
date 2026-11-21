from netmiko import ConnectHandler
x = 18
switch = {
    "device_type": "cisco_ios",
    "host": f"172.16.{x}.4",
    "username": "student",
    "password": "pxl"
}
vlan_namen = {
    int(f"1{x}"): "Management",
    int(f"2{x}"): "VM-Hosts",
    int(f"3{x}"): "Appliance-Servers",
    int(f"4{x}"): "Data-Users",
    99: "Native-Vlan",
}
poorten = {
    "GigabitEthernet1/0/1-5":   int(f"2{x}"),
    "GigabitEthernet1/0/6-10":  int(f"3{x}"),
    "GigabitEthernet1/0/11-20": int(f"4{x}"),
    "GigabitEthernet1/0/21-22": int(f"1{x}"),
}
commands = [f"hostname LAB-SR{x}-SW01"]
for vlan_id, naam in vlan_namen.items():
    commands.extend([
        f"vlan {vlan_id}",
        f"name {naam}",
    ])

for bereik, vlan_id in poorten.items():
    commands.extend([
        f"interface range {bereik}";
        "switchport mode access",
        f"switchport access vlan {vlan_id}",
        "no shutdown",
    ])
commands.extend([
    "interface range GigabitEthernet1/0/23-24",
    "switchport mode trunk",
    "switchport trunk native vlan 99",
    f"switchport trunk allowed vlan 99,1{x},2{x},3{x},4{x}",
    "no shutdown",
])
#Toon wat er verstuurd wordt
for c in commands:
    print(c)

connection = ConnectHandler(**switch)
output = connection.send_config_set(commands)
print(output)
#print(connection.save_config())
connection.disconnect()


