"""
LAB 3 - Deel 6: Network Discovery

Overloopt alle outer-adressen 10.199.66.201 - .222 (tafel 1 t/m 22),
haalt per router hostname, interfaces, routes en OSPF-buren op
en drukt een overzicht af.
"""
import re
import socket
from netmiko import ConnectHandler

# ------------------------------------------------------------------
# Instellingen
# ------------------------------------------------------------------
USERNAME = "student"
PASSWORD = "pxl"

# Outer interfaces: 10.199.66.(200 + tafelnummer), tafels 1 t/m 22
KANDIDATEN = [f"10.199.66.{200 + tafel}" for tafel in range(1, 23)]

# Route die we op elke router willen terugvinden (vraag 2c)
ZOEK_ROUTE = "172.16.18.192/26"   # VLAN 418 van tafel 18


# ------------------------------------------------------------------
# Hulpfuncties
# ------------------------------------------------------------------
def ssh_open(ip, timeout=1.5):
    """Snel testen of poort 22 openstaat, zodat we niet lang wachten
    op adressen waar geen router zit."""
    try:
        with socket.create_connection((ip, 22), timeout=timeout):
            return True
    except OSError:
        return False


def parse_ospf_neighbors(output):
    """'show ip ospf neighbor' -> lijst van dicts met router-id, state en adres.

    Neighbor ID     Pri   State           Dead Time   Address         Interface
    19.19.19.19       1   FULL/DR         00:00:35    10.199.66.219   GigabitEthernet0/0/1
    """
    buren = []
    for line in output.splitlines():
        parts = line.split()
        # een buurregel begint met een router-id (x.x.x.x) en heeft min. 6 kolommen
        if len(parts) >= 6 and re.match(r"^\d+\.\d+\.\d+\.\d+$", parts[0]):
            buren.append({
                "router_id": parts[0],
                "state": parts[2],
                "adres": parts[-2],
            })
    return buren


def parse_ospf_routes(output):
    """'show ip route' -> lijst van prefixen die via OSPF geleerd zijn.

    O        172.16.19.192/26 [110/2] via 10.199.66.219, 00:10:11, Gi0/0/1
    O*E2     0.0.0.0/0 [110/1] via 10.199.66.200, ...
    O IA     ...
    """
    routes = []
    for line in output.splitlines():
        if re.match(r"^O[\s*]", line):                 # regel begint met O, O*, O IA, O E2 ...
            prefix = re.search(r"\d+\.\d+\.\d+\.\d+/\d+", line)
            if prefix:
                routes.append(prefix.group())
    return routes


def route_aanwezig(routes, prefix):
    """Vraag 2c: staat een bepaalde route in de lijst van OSPF-routes?"""
    return prefix in routes


def ontdek(ip):
    """Verbind met één router en haal alle info op."""
    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": USERNAME,
        "password": PASSWORD,
    }
    with ConnectHandler(**device) as conn:
        return {
            "ip": ip,
            "hostname": conn.find_prompt().rstrip("#>"),
            "int_brief": conn.send_command("show ip interface brief"),
            "route": conn.send_command("show ip route"),
            "ospf_nb": conn.send_command("show ip ospf neighbor"),
        }


# ------------------------------------------------------------------
# 1. Routers ontdekken
# ------------------------------------------------------------------
routers = []
for ip in KANDIDATEN:
    if not ssh_open(ip):
        continue                                    # geen router op dit adres
    try:
        info = ontdek(ip)
        info["buren"] = parse_ospf_neighbors(info["ospf_nb"])
        info["routes"] = parse_ospf_routes(info["route"])
        routers.append(info)
        print(f"[OK]   {ip} -> {info['hostname']}")
    except Exception as e:
        print(f"[FOUT] {ip}: {e}")

# Opzoektabel: outer-IP -> hostname, om buren met een naam te tonen
naam_van_ip = {r["ip"]: r["hostname"] for r in routers}

# ------------------------------------------------------------------
# 2. Overzicht
# ------------------------------------------------------------------
print("\n===== NETWORK DISCOVERY =====")
for r in routers:
    buur_namen = [naam_van_ip.get(b["adres"], b["router_id"]) for b in r["buren"]]
    aanwezig = route_aanwezig(r["routes"], ZOEK_ROUTE)

    print(f"\n{r['hostname']} {r['ip']}")
    print(f"OSPF neighbors: {', '.join(buur_namen) or 'geen'}")
    print(f"OSPF routes: {len(r['routes'])}")
    for route in r["routes"]:
        print(f"    {route}")
    print(f"Route {ZOEK_ROUTE} aanwezig: {'JA' if aanwezig else 'NEE'}")

print(f"\n===== {len(routers)} routers gevonden =====")