import socket
import threading
import json
import time


class NetPeer:
    def __init__(self, bind_port=12000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', bind_port))
        self.peers = set()
        self.running = False
        self.on_message = None

    def start(self):
        self.running = True
        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()

    def _recv_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self.peers.add(addr)
                try:
                    msg = json.loads(data.decode('utf8'))
                except Exception:
                    msg = None
                if self.on_message:
                    self.on_message(msg, addr)
            except Exception:
                pass

    def send(self, obj, addr):
        try:
            self.sock.sendto(json.dumps(obj).encode('utf8'), addr)
        except Exception:
            pass

    def broadcast(self, obj):
        for p in list(self.peers):
            self.send(obj, p)

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass
