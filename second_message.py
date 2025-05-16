import sqlite3
import requests
from datetime import datetime
from time import sleep

# Configurações
DB_PATH = "whatsapp_messages.db"
API_URL = "http://localhost:8081/message/sendText/{}"

def format_phone(phone):
    if not phone:
        return None
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) == 11:
        return f"+55{phone}"
    return None

def send_whatsapp_message(phone, message, instance_name, token):
    headers = {"apikey": token}
    payload = {
        "number": phone,
        "text": message,
        "delay": 5
    }
    try:
        response = requests.post(API_URL.format(instance_name), json=payload, headers=headers)
        print(f"Resposta da API para {phone}: {response.status_code}")
        return response.status_code == 201
    except requests.RequestException as e:
        print(f"Erro ao enviar mensagem: {e}")
        return False

def send_second_messages():
    today = datetime.now().strftime("%d/%m/%Y")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.us_at, a.razao_social, a.nome_profissional, a.cbo_profissional, 
               a.data_agendamento, a.codigo, a.usuario, a.nome_usuario, a.telefone, 
               a.telefone_celular, a.telefone_contato, a.motivo_consulta, a.horario, 
               a.inclusao, a.complemento_unidade, a.numero_unidade, a.municipio, 
               a.bairro, a.logradouro, a.instance_id, a.first_message_sent, 
               a.second_message_sent, a.second_message_date, a.data_envio,
               im.instance_name, im.token
        FROM appointments a
        JOIN instance_mapping im ON a.instance_id = im.instance_id
        WHERE a.second_message_date = ? AND a.second_message_sent = 'PENDENTE'
    ''', (today,))
    
    appointments = cursor.fetchall()
    
    for appt in appointments:
        (
            id, us_at, razao_social, nome_profissional, cbo_profissional,
            data_agendamento, codigo, usuario, nome_usuario, telefone,
            telefone_celular, telefone_contato, motivo_consulta, horario,
            inclusao, complemento_unidade, numero_unidade, municipio,
            bairro, logradouro, instance_id, first_message_sent,
            second_message_sent, second_message_date, data_envio,
            instance_name, token
        ) = appt
        
        phone = format_phone(telefone_celular) or format_phone(telefone) or format_phone(telefone_contato)
        if not phone:
            print(f"Telefone inválido para usuário: {nome_usuario}")
            cursor.execute('UPDATE appointments SET second_message_sent = ? WHERE id = ?', ('FALHA', id))
            conn.commit()
            continue
        
        message = (
            f"Olá, {nome_usuario}, Sou a Assistente Virtual de Agendamentos da Secretaria Municipal de Saúde de Bebedouro.\n\n"
            f"Lembrete: sua consulta está marcada para {data_agendamento} às {horario} \n\n"
            f"Com {nome_profissional.upper()}, {cbo_profissional.upper()}.\n\n"
            f"Podemos confirmar sua presença?\n\n"
            f"LOCAL DE ATENDIMENTO: {razao_social} \n\n"
            f"RUA {logradouro.upper()} - {numero_unidade}, {bairro.upper()}, {municipio.upper()}"
        )
        
        second_message_status = 'ENVIADO' if send_whatsapp_message(phone, message, instance_name, token) else 'FALHA'
        
        cursor.execute('UPDATE appointments SET second_message_sent = ? WHERE id = ?', (second_message_status, id))
        conn.commit()
        
        print(f"Segunda mensagem para {phone}: {second_message_status}")
    
    conn.close()

if __name__ == "__main__":
    print("Iniciando verificação de mensagens de lembrete...")
    while True:
        send_second_messages()
        sleep(3600)