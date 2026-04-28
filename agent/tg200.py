
import socket
import time
import urllib.parse


class TG200Client:
    def __init__(self, host, port, username, password, timeout=10):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

        login_cmd = (
            f"Action: Login\r\n"
            f"Username: {self.username}\r\n"
            f"Secret: {self.password}\r\n\r\n"
        )

        self.sock.sendall(login_cmd.encode())
        response = self._read_some()

        if "Response: Success" not in response:
            raise Exception(f"TG200 login failed: {response}")

        return True

    def send_sms(self, gsm_port, to_number, message, message_id):
        safe_message = urllib.parse.quote(message)

        cmd = (
            "Action: smscommand\r\n"
            f"command: gsm send sms {gsm_port} {to_number} \"{safe_message}\" {message_id}\r\n\r\n"
        )

        self.sock.sendall(cmd.encode())
        response = self._read_until_marker("--END SMS EVENT--", timeout=30)

        return {
            "success": "Status: 1" in response,
            "raw": response
        }

    def listen_once(self):
        try:
            data = self.sock.recv(4096).decode(errors="ignore")
            if "Event: ReceivedSMS" in data:
                return self._parse_received_sms(data)
        except socket.timeout:
            return None
        return None

    def _read_some(self):
        time.sleep(0.5)
        return self.sock.recv(4096).decode(errors="ignore")

    def _read_until_marker(self, marker, timeout=30):
        old_timeout = self.sock.gettimeout()
        self.sock.settimeout(timeout)

        data = ""
        start = time.time()

        while marker not in data and time.time() - start < timeout:
            try:
                chunk = self.sock.recv(4096).decode(errors="ignore")
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break

        self.sock.settimeout(old_timeout)
        return data

    def _parse_received_sms(self, raw):
        result = {"raw": raw}

        for line in raw.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()

        return {
            "id": result.get("ID"),
            "gsm_port": result.get("GsmPort"),
            "sender": result.get("Sender"),
            "received_at": result.get("Recvtime"),
            "smsc": result.get("Smsc"),
            "content": urllib.parse.unquote(result.get("Content", "")),
            "raw": raw
        }

    def close(self):
        if self.sock:
            self.sock.close()
