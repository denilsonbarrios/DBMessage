import subprocess
import json
import requests
from time import sleep

# Configurações
WHATSAPP_API_URL = "http://localhost:8081/message/sendText/TesteWebApp"
WHATSAPP_TOKEN = "3A0C6E4B89B9-4625-8FAB-487529276421"
NOTIFICATION_PHONE = "+5517991406399"  # Número para receber notificações
CHECK_INTERVAL = 300  # Intervalo de verificação em segundos (5 minutos)

def get_pm2_status():
    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
        processes = json.loads(result.stdout)
        return processes
    except Exception as e:
        print(f"Erro ao obter status do PM2: {e}")
        return []

def send_whatsapp_notification(message):
    headers = {"apikey": WHATSAPP_TOKEN}
    payload = {
        "number": NOTIFICATION_PHONE,
        "text": message,
    }
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        print(f"Notificação WhatsApp enviada: {response.status_code} - {response.text}")
        return response.status_code == 201
    except requests.RequestException as e:
        print(f"Erro ao enviar notificação WhatsApp: {e}")
        return False

def monitor_services():
    monitored_processes = ['backend', 'process-csv', 'send-second-message']
    previous_status = {proc: 'online' for proc in monitored_processes}
    
    while True:
        processes = get_pm2_status()
        for proc in processes:
            name = proc['name']
            if name not in monitored_processes:
                continue
            
            status = proc['pm2_env']['status']
            if status != previous_status[name] and status != 'online':
                message = f"🚨 Alerta: O serviço '{name}' está fora do ar! Status atual: {status}. Verifique imediatamente."
                send_whatsapp_notification(message)
                print(f"Serviço {name} caiu (status: {status}). Notificação enviada.")
            
            previous_status[name] = status
        
        sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    print("Iniciando monitoramento de serviços...")
    monitor_services()