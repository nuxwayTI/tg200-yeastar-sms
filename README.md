# TG200 Yeastar SMS Provider

Sistema para integrar Yeastar P-Series Cloud SMS Channel con gateway GSM Yeastar TG200.

## Arquitectura

Yeastar Cloud -> Render FastAPI -> Agente local -> TG200 -> SMS GSM

## Backend Render

Servicio recomendado en Render:

Web Service

Configuración:

Root Directory:

backend

Build Command:

pip install -r requirements.txt

Start Command:

uvicorn main:app --host 0.0.0.0 --port $PORT

Variables de entorno:

API_KEY=clave-secreta
YEASTAR_WEBHOOK_URL=webhook-copiado-desde-yeastar

## Yeastar

En Messaging > Message Channel > Add SMS:

Name:

TG200 SMS

ITSP:

General

API Key:

mismo valor de API_KEY

API Address for Sending Messages:

https://TU-SERVICIO.onrender.com/sendmessage

API Address for Verifying Authentication:

https://TU-SERVICIO.onrender.com/verify

## Agente local

Copiar:

agent/config.example.json

como:

agent/config.json

Editar:

server_url
api_key
tg_host
tg_user
tg_pass
gsm_port

Ejecutar:

python agent.py

## Compilar EXE

En Windows:

cd agent
pip install -r requirements.txt
pyinstaller --onefile agent.py

El EXE queda en:

dist/agent.exe
