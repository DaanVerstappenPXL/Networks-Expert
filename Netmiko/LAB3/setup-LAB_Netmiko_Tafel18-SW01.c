en
conf t
hostname LAB-SR18-SW01
no ip domain lookup
ip domain name student.local
username student privilege 15 secret pxl
crypto key generate rsa modulus 2048
vlan 118
name Management
vlan 99
name Native
exit
line vty 0 4
login local
transport input ssh
exit
int g1/0/24
switchport mode trunk
switchport trunk native vlan 99
int g1/0/22
switchport mode access
switchport access vlan 118
int vlan 118
ip add 172.16.18.4 255.255.255.192
no shut
exit
ip default-gateway 172.16.18.2
