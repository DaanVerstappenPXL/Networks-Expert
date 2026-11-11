en
conf t
hostname LAB-SR18-R01
no ip domain lookup
ip domain name student.local
username student privilege 15 secret pxl
crypto key generate rsa modulus 2048
line vty 0 4
login local
transport input ssh
exit
int g0/0/0
no shut
int g0/0/0.118
encapsulation dot1q 118
ip add 172.16.18.2 255.255.255.192
no shut
