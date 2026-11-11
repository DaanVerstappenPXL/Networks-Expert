from netmiko import ConnectHandler

print("===== NETWORK DISCOVERY =====")

# Loop door mogelijke tafels (bijv. tafel 1 t/m 20 -> 10.199.66.201 t/m .220)
for tafel in range(1, 21):
    ip = f"10.199.66.{200 + tafel}"
    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": "student",
        "password": "pxl",
        "timeout": 3
    }
    try:
        conn = ConnectHandler(**device)
        prompt = conn.find_prompt().replace("#", "").replace(">", "")
        ospf_neighbors = conn.send_command("show ip ospf neighbor")
        ospf_routes = conn.send_command("show ip route ospf")
        conn.disconnect()

        # Tel aantal OSPF routes (regels die starten met 'O')
        route_count = sum(1 for line in ospf_routes.splitlines() if line.strip().startswith("O"))
        
        # Haal Neighbor ID's op
        neighbors = [line.split()[0] for line in ospf_neighbors.splitlines()[1:] if line.strip()]
        
        print(f"{prompt} ({ip})")
        print(f"  OSPF neighbors: {', '.join(neighbors) if neighbors else 'Geen'}")
        print(f"  OSPF routes: {route_count}\n")
    except Exception:
        # Router van deze tafel staat uit of is niet bereikbaar
        pass
