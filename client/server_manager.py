import json
import os
import socket
from typing import Dict, List


class ServerManager:
    def __init__(self):
        self.config_file = "servers.json"
        self.servers: List[Dict] = []
        self.load_servers()

    def get_local_ip(self) -> str:
        """Get the local IP address"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            return "localhost"

    def load_servers(self):
        """Load server list from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.servers = data.get("servers", [])
            except (json.JSONDecodeError, FileNotFoundError):
                self.servers = []

        # Add default server if list is empty
        if not self.servers:
            default_server = {
                "name": "ローカルサーバー",
                "address": f"{self.get_local_ip()}:8000",
            }
            self.servers.append(default_server)
            self.save_servers()

    def save_servers(self):
        """Save server list to file"""
        data = {"servers": self.servers}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save servers: {e}")

    def add_server(self, name: str, address: str) -> bool:
        """Add a new server to the list"""
        # Check if server already exists
        for server in self.servers:
            if server["address"] == address:
                return False

        self.servers.append({"name": name, "address": address})
        self.save_servers()
        return True

    def remove_server(self, index: int) -> bool:
        """Remove server by index"""
        if 0 <= index < len(self.servers):
            self.servers.pop(index)
            self.save_servers()
            return True
        return False

    def get_servers(self) -> List[Dict]:
        """Get all servers"""
        return self.servers.copy()

    def get_default_address(self) -> str:
        """Get default server address"""
        if self.servers:
            return self.servers[0]["address"]
        return f"{self.get_local_ip()}:8000"
