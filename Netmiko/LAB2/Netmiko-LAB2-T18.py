from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "172.16.18.2",
    "username": "student",
    "password": "pxl"
}

connection = ConnectHandler(**device)

print("Verbonden met de router!")

output = connection.send_command("show ip interface brief")

print(output)

connection.disconnect()
