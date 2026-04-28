
import json
import time
import requests
from tg200 import TG200Client


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_config()

    tg = TG200Client(
        host=cfg["tg_host"],
        port=cfg.get("tg_port", 5038),
        username=cfg["tg_user"],
        password=cfg["tg_pass"]
    )

    print("Conectando al TG200...")
    tg.connect()
    print("TG200 conectado correctamente.")

    server_url = cfg["server_url"].rstrip("/")
    api_key = cfg["api_key"]
    agent_id = cfg["agent_id"]
    gsm_port = cfg.get("gsm_port", 2)
    poll_seconds = cfg.get("poll_seconds", 5)

    while True:
        try:
            response = requests.get(
                f"{server_url}/agent/poll",
                params={
                    "agent_id": agent_id,
                    "agent_key": api_key
                },
                timeout=20
            )

            response.raise_for_status()
            job = response.json().get("job")

            if job:
                print("Enviando SMS:", job["to"], job["text"])

                result = tg.send_sms(
                    gsm_port=gsm_port,
                    to_number=job["to"].replace("+", ""),
                    message=job["text"],
                    message_id=job["id"]
                )

                requests.post(
                    f"{server_url}/agent/result",
                    params={"agent_key": api_key},
                    json={
                        "id": job["id"],
                        "success": result["success"],
                        "raw": result["raw"]
                    },
                    timeout=20
                )

                print("Resultado:", result["success"])

            inbound = tg.listen_once()

            if inbound:
                print("SMS recibido:", inbound)

                requests.post(
                    f"{server_url}/agent/inbound",
                    params={"agent_key": api_key},
                    json=inbound,
                    timeout=20
                )

        except Exception as e:
            print("ERROR:", str(e))
            time.sleep(5)

        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
