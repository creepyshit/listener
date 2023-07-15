import socket

target_host = "www.google.com"
target_port = 80

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(b"AAABBBCCC", (target_host, target_port))
print("UDP packet sent to {}:{}".format(target_host, target_port))

try:
    data, addr = client.recvfrom(4096)
    print("Response received from {}:{}".format(addr[0], addr[1]))
    print(data.decode())
except socket.timeout:
    print("Socket timeout occurred. No response received.")
except Exception as e:
    print("An error occurred:", str(e))

client.close()
