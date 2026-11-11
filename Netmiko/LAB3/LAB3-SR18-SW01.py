from netmiko import ConnectHandler

# ============================================================
# DEVICE INFORMATION
# ============================================================

device = {
    "device_type": "cisco_ios",
    "host": "172.16.18.4",  # Management IP van SW1 (Tafel 18)
    "username": "student",
    "password": "pxl",
}

# ============================================================
# VLAN & POORT INSTELLINGEN (Tafel 18)
# ============================================================

vlans = {
    118: "Management",
    218: "VM-Hosts",
    318: "Appliance-Servers",
    418: "Data-Users",
    99: "Native",
}

# LET OP BIJ FYSIEKE SWITCH IN HET LOKAAL:
# In het .c setup-bestand staat "GigabitEthernet1/0/" (vaak op fysieke Catalyst switches).
# In het Python-voorbeeldscript stond "GigabitEthernet0/" (vaak op virtuele switches).
# Check op de switch met 'show ip interface brief' welke naamgeving gebruikt wordt
# en pas indien nodig deze variabele hieronder op 1 plek aan:
PORT_PREFIX = "GigabitEthernet1/0/"  # Verander naar "GigabitEthernet0/" indien nodig

# LET OP BIJ HOSTNAME:
# Tafel 18 zit op Student Rack 3 (LAB-SR3-SW01) of gebruikt het tafelnummer (LAB-SR18-SW01).
SWITCH_HOSTNAME = "LAB-SR18-SW01"

# ============================================================
# CONNECT
# ============================================================

connection = ConnectHandler(**device)

print("Connected to:", connection.find_prompt())

# ============================================================
# CONFIGURATION
# ============================================================

commands = []

# Hostname
commands.append(f"hostname {SWITCH_HOSTNAME}")

# ------------------------------------------------------------
# VLANs aanmaken
# ------------------------------------------------------------

for vlan, name in vlans.items():
    commands.extend([
        f"vlan {vlan}",
        f"name {name}",
        "exit",
    ])

# ------------------------------------------------------------
# Access ports configureren
# ------------------------------------------------------------

# Poorten 1-5: VLAN 218
commands.extend([
    f"interface range {PORT_PREFIX}1-5",
    "switchport mode access",
    "switchport access vlan 218",
    "no shutdown",
    "exit",
])

# Poorten 6-10: VLAN 318
commands.extend([
    f"interface range {PORT_PREFIX}6-10",
    "switchport mode access",
    "switchport access vlan 318",
    "no shutdown",
    "exit",
])

# Poorten 11-20: VLAN 418
commands.extend([
    f"interface range {PORT_PREFIX}11-20",
    "switchport mode access",
    "switchport access vlan 418",
    "no shutdown",
    "exit",
])

# Poorten 21-22: VLAN 118
commands.extend([
    f"interface range {PORT_PREFIX}21-22",
    "switchport mode access",
    "switchport access vlan 118",
    "no shutdown",
    "exit",
])

# ------------------------------------------------------------
# Trunk naar de router
# ------------------------------------------------------------

commands.extend([
    f"interface range {PORT_PREFIX}23-24",
    "switchport mode trunk",
    "switchport trunk allowed vlan 118,218,318,418,99",
    "switchport trunk native vlan 99",
    "no shutdown",
    "exit",
])

# ============================================================
# SEND CONFIGURATION
# ============================================================

print("\nConfiguring SW1...\n")
output = connection.send_config_set(commands)
print(output)

# ============================================================
# VERIFICATION
# ============================================================

print("\n========================================")
print("VLAN STATUS")
print("========================================")
print(connection.send_command("show vlan brief"))

print("\n========================================")
print("TRUNK STATUS")
print("========================================")
print(connection.send_command("show interfaces trunk"))

print("\n========================================")
print("INTERFACE STATUS")
print("========================================")
print(connection.send_command("show ip interface brief"))

print("\n========================================")
print("RUNNING CONFIGURATION")
print("========================================")
print(connection.send_command("show running-config"))

# ============================================================
# DISCONNECT
# ============================================================

connection.disconnect()
print("\nDisconnected.")
