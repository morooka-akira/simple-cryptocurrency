import socket

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 環境に合わせた接続先を設定
my_socket.connect(('192.168.11.3', 50030))
my_text = "Hello! This is test message from my sample client!"
my_socket.sendall(my_text.encode('utf-8'))
