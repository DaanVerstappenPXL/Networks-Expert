from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "172.16.18.2",
    "username": "student",
    "password": "pxl"
}

connection = ConnectHandler(**device)
output = connection.send_command("show ip interface brief")
connection.disconnect()

up_list, down_list, admin_down_list = [], [], []

for line in output.splitlines()[1:]:
    if not line.strip():
        continue
    parts = line.split()
    intf_name = parts[0]
    
    if "administratively down" in line.lower():
        admin_down_list.append(intf_name)
    elif parts[-2].lower() == "up" and parts[-1].lower() == "up":
        up_list.append(intf_name)
    else:
        down_list.append(intf_name)

print(f"UP ({len(up_list)}): {', '.join(up_list)}")
print(f"DOWN ({len(down_list)}): {', '.join(down_list)}")
print(f"ADMIN DOWN ({len(admin_down_list)}): {', '.join(admin_down_list)}")
