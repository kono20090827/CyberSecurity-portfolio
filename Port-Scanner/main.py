import socket

target = "127.0.0.1"

print("開始掃描：", target)

for port in range(1, 1025):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.settimeout(0.1)

    result = s.connect_ex((target, port))

    if result == 0:
        print("開放 Port:", port)

    s.close()

print("掃描完成")
