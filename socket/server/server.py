#!/usr/bin/env python3
import socket
from server_module import parsing, sql_utils

HOST = '0.0.0.0'
PORT = 9999

def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            try:
                packet = parsing.parse_packet(data.decode('utf-8'))
                sql_utils.insert_sensor_data(packet)
                conn.sendall(b"ACK\n")
            except Exception as e:
                print(f"패킷 처리 실패: {e}")
                conn.sendall(b"ERROR\n")
    print(f"[연결 종료] {addr}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"서버 시작 {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    main()
