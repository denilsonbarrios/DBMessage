import csv
import sqlite3
import requests
import os
import glob
from datetime import datetime, timedelta
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configurações
CSV_DIRECTORY = "csv/"
DB_PATH = "whatsapp_messages.db"
API_URL = "http://localhost:8081/message/sendText/{}"

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            us_at TEXT,
            razao_social TEXT,
            nome_profissional TEXT,
            cbo_profissional TEXT,
            data_agendamento TEXT,
            codigo TEXT,
            usuario TEXT,
            nome_usuario TEXT,
            telefone TEXT,
            telefone_celular TEXT,
            telefone_contato TEXT,
            motivo_consulta TEXT,
            horario TEXT,
            inclusao TEXT,
            complemento_unidade TEXT,
            numero_unidade TEXT,
            municipio TEXT,
            bairro TEXT,
            logradouro TEXT,
            instance_id TEXT,
            first_message_sent TEXT DEFAULT 'PENDENTE',
            second_message_sent TEXT DEFAULT 'PENDENTE',
            second_message_date TEXT,
            data_envio TEXT,
            UNIQUE(usuario, inclusao, data_agendamento)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instance_mapping (
            us_at TEXT PRIMARY KEY,
            instance_id TEXT NOT NULL,
            instance_name TEXT NOT NULL,
            token TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT OR REPLACE INTO instance_mapping (us_at, instance_id, instance_name, token)
        VALUES (?, ?, ?, ?)
    ''', ('2', '9cb57386-120e-40fb-b112-6c901fa6e00a', 'TesteWebApp', '3A0C6E4B89B9-4625-8FAB-487529276421'))
    conn.commit()
    conn.close()
    print("Banco de dados configurado em whatsapp_messages.db.")

def check_duplicates(usuario, inclusao, data_agendamento):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, data_agendamento, horario, nome_usuario
        FROM appointments
        WHERE usuario = ? AND inclusao = ? AND data_agendamento = ?
    ''', (usuario, inclusao, data_agendamento))
    result = cursor.fetchone()
    conn.close()
    return result

def parse_csv(csv_file):
    data = []
    print(f"Parseando {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        headers = reader.fieldnames
        print(f"Cabeçalhos encontrados: {headers}")
        
        for row_idx, row in enumerate(reader):
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, list):
                    v = ';'.join(str(x) for x in v)
                elif v is None:
                    v = ''
                cleaned_row[k] = v.strip() if isinstance(v, str) else str(v)
            
            if all(not v for v in cleaned_row.values()):
                print(f"Linha {row_idx + 1} vazia ou sem dados, ignorada.")
                continue
            
            print(f"Linha {row_idx + 1}: {cleaned_row}")
            
            item = {
                'us_at': cleaned_row.get('U.S.At.', ''),
                'razao_social': cleaned_row.get('Razão Social da Unidade de Saúde de Aten', ''),
                'nome_profissional': cleaned_row.get('Nome do Profissional', ''),
                'cbo_profissional': cleaned_row.get('Descrição do CBO Profissional', '').upper(),
                'data_agendamento': cleaned_row.get('Data', ''),
                'codigo': cleaned_row.get('Código', ''),
                'usuario': cleaned_row.get('Usuário', ''),
                'nome_usuario': cleaned_row.get('Nome do Usuário', ''),
                'telefone': cleaned_row.get('Telefone', ''),
                'telefone_celular': cleaned_row.get('Tel.Celular', ''),
                'telefone_contato': cleaned_row.get('Tel.Contato', ''),
                'motivo_consulta': cleaned_row.get('Descrição Motivo da Consulta', ''),
                'horario': cleaned_row.get('Horário', '')[:5],
                'inclusao': cleaned_row.get('Inclusão', ''),
                'complemento_unidade': cleaned_row.get('Complemento da Un. de Atendimento', ''),
                'numero_unidade': cleaned_row.get('Número da Unidade de Atendimento', ''),
                'municipio': capitalize_words(cleaned_row.get('Nome do Município da Un. Atendimento', '')),
                'bairro': cleaned_row.get('Nome do Bairro Un. Atendimento', ''),
                'logradouro': cleaned_row.get('Nome do Logradouro da Un. Atendimento', '')
            }
            
            if item['usuario'] and item['inclusao'] and item['razao_social']:
                data.append(item)
            else:
                print(f"Linha {row_idx + 1} ignorada: faltam campos chave (usuario, inclusao, razao_social).")
    
    print(f"Total de registros extraídos: {len(data)}")
    return data

def format_phone_number(phone):
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits != '99999999999':
        return f"+55{digits}"
    return None

def select_phone(telefone_celular, telefone_contato, telefone):
    for phone in [telefone_celular, telefone_contato, telefone]:
        formatted = format_phone_number(phone)
        if formatted:
            return formatted
    return None

def capitalize_words(text):
    return ' '.join(word.capitalize() for word in text.split())

def calculate_second_message_date(appointment_date):
    try:
        date_obj = datetime.strptime(appointment_date, "%d/%m/%Y")
        second_message_date = date_obj - timedelta(days=4)
        return second_message_date.strftime("%d/%m/%Y")
    except ValueError:
        return None

def calculate_days_difference(date_str1, date_str2):
    try:
        date1_str = date_str1.split(' ')[0]
        date1 = datetime.strptime(date1_str, "%d/%m/%Y")
        date2 = datetime.strptime(date_str2, "%d/%m/%Y")
        delta = (date2 - date1).days
        return delta
    except ValueError as e:
        print(f"Erro ao calcular diferença de dias: {e}")
        return None

def get_instance_for_us_at(us_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT instance_id, instance_name, token FROM instance_mapping WHERE us_at = ?", (us_at,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None, None)

def send_whatsapp_message(phone, message, instance_name, token):
    headers = {"apikey": token}
    payload = {
        "number": phone,
        "text": message,
        "delay": 5000
    }
    try:
        response = requests.post(API_URL.format(instance_name), json=payload, headers=headers)
        print(f"Resposta da API para {phone}: {response.status_code} - {response.text}")
        return response.status_code == 201
    except requests.RequestException as e:
        print(f"Erro ao enviar mensagem: {e}")
        return False

def insert_data_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    for item in data:
        duplicate = check_duplicates(item['usuario'], item['inclusao'], item['data_agendamento'])
        if duplicate:
            print(f"Registro duplicado encontrado: ID {duplicate[0]}, "
                  f"Data Agendamento: {duplicate[1]}, Horário: {duplicate[2]}, "
                  f"Nome: {duplicate[3]}")
            continue
        
        instance_id, instance_name, token = get_instance_for_us_at(item['us_at'])
        if not instance_id or not instance_name or not token:
            print(f"Instância não encontrada para us_at: {item['us_at']}")
            continue
        
        second_message_date = calculate_second_message_date(item['data_agendamento'])
        if not second_message_date:
            print(f"Data de agendamento inválida para {item['nome_usuario']}: {item['data_agendamento']}")
            continue
        
        cursor.execute('''
            INSERT OR IGNORE INTO appointments (
                us_at, razao_social, nome_profissional, cbo_profissional, data_agendamento, codigo,
                usuario, nome_usuario, telefone, telefone_celular, telefone_contato,
                motivo_consulta, horario, inclusao, complemento_unidade, numero_unidade,
                municipio, bairro, logradouro, instance_id, first_message_sent,
                second_message_sent, second_message_date, data_envio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['us_at'], item['razao_social'], item['nome_profissional'], item['cbo_profissional'],
            item['data_agendamento'], item['codigo'], item['usuario'],
            item['nome_usuario'], item['telefone'], item['telefone_celular'],
            item['telefone_contato'], item['motivo_consulta'], item['horario'],
            item['inclusao'], item['complemento_unidade'], item['numero_unidade'],
            item['municipio'], item['bairro'], item['logradouro'],
            instance_id, 'PENDENTE', 'PENDENTE', second_message_date,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        if cursor.rowcount > 0:
            inserted += 1
            appt_id = cursor.lastrowid
            conn.commit()
            
            nome = item['nome_usuario']
            data = item['data_agendamento']
            horario = item['horario']
            profissional = item['nome_profissional']
            especialidade = item['cbo_profissional']
            razao_social = item['razao_social']
            logradouro = item['logradouro']
            numero_unidade = item['numero_unidade']
            bairro = item['bairro']
            municipio = item['municipio']
            
            formatted_phone = select_phone(item['telefone_celular'], item['telefone_contato'], item['telefone'])
            if not formatted_phone:
                cursor.execute('''
                    UPDATE appointments
                    SET first_message_sent = 'FALHA', data_envio = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
                print(f"Telefone inválido para {nome}: {item['telefone_celular']}, {item['telefone_contato']}, {item['telefone']}")
                conn.commit()
                continue
            
            days_difference = calculate_days_difference(item['inclusao'], second_message_date)
            if days_difference is None:
                print(f"Erro ao calcular diferença de dias para {nome}, enviando primeira mensagem normalmente.")
                days_difference = 5
            
            if days_difference <= 4:
                print(f"Inclusão próxima da second_message_date ({days_difference} dias) para {nome}, enviando apenas o lembrete.")
                cursor.execute('''
                    UPDATE appointments
                    SET first_message_sent = 'NÃO ENVIADO', data_envio = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
                conn.commit()
                
                mensagem = (
                    f"Olá, {nome}, Sou a Assistente Virtual de Agendamentos da Secretaria Municipal de Saúde de Bebedouro.\n\n"
                    f"Lembrete: sua consulta está marcada para {data} às {horario} "
                    f"com {profissional}, {especialidade}.\n\n"
                    f"Podemos confirmar sua presença?\n\n"
                    f"LOCAL DE ATENDIMENTO: {razao_social}, {municipio}."
                )
                
                second_message_status = 'ENVIADO' if send_whatsapp_message(formatted_phone, mensagem, instance_name, token) else 'FALHA'
                
                cursor.execute('''
                    UPDATE appointments
                    SET second_message_sent = ?, data_envio = ?
                    WHERE id = ?
                ''', (second_message_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
                print(f"Lembrete (segunda mensagem) para {formatted_phone}: {second_message_status}")
            else:
                print(f"Inclusão a mais de 4 dias da second_message_date ({days_difference} dias) para {nome}, enviando primeira mensagem.")
                mensagem = (
                    f"Olá, {nome}, Sou a Assistente Virtual de Agendamentos da Secretaria Municipal de Saude de Bebedouro.\n\n"
                    f"Estamos entrando em contato para confirmar o seu agendamento do dia {data} às {horario} com o {profissional}, {especialidade}.\n\n"
                    f"LOCAL DE ATENDIMENTO: {razao_social}, Rua {logradouro} - {numero_unidade}, {bairro}, {municipio}"
                )
                
                first_message_status = 'ENVIADO' if send_whatsapp_message(formatted_phone, mensagem, instance_name, token) else 'FALHA'
                
                cursor.execute('''
                    UPDATE appointments
                    SET first_message_sent = ?, data_envio = ?
                    WHERE id = ?
                ''', (first_message_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
                print(f"Primeira mensagem para {formatted_phone}: {first_message_status}")
            
            conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total_records = cursor.fetchone()[0]
    print(f"Total de registros no banco após inserção: {total_records}")
    
    cursor.execute('SELECT id, usuario, inclusao, razao_social, nome_usuario, instance_id, first_message_sent, second_message_sent FROM appointments LIMIT 5')
    sample_records = cursor.fetchall()
    print("Amostra de registros inseridos:")
    for record in sample_records:
        print(f"ID: {record[0]}, Usuário: {record[1]}, Inclusão: {record[2]}, Razão Social: {record[3]}, Nome: {record[4]}, Instance ID: {record[5]}, First Message: {record[6]}, Second Message: {record[7]}")
    
    conn.close()
    print(f"{inserted} registros inseridos no banco.")
    return inserted

def process_csv_folder(csv_folder='csv'):
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
    
    csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
    
    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado em {csv_folder}")
        return
    
    for csv_file in csv_files:
        print(f"Processando {csv_file}...")
        try:
            report_data = parse_csv(csv_file)
            inserted = insert_data_to_db(report_data)
            print(f"{inserted} registros inseridos do arquivo {csv_file}.")
        except Exception as e:
            print(f"Erro ao processar {csv_file}: {str(e)}")
        finally:
            os.remove(csv_file)
            print(f"Arquivo {csv_file} removido com sucesso.")

class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            print(f"Novo arquivo CSV detectado: {event.src_path}")
            process_csv_folder()

def main():
    setup_database()
    
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, CSV_DIRECTORY, recursive=False)
    observer.start()
    print(f"Monitorando diretório: {CSV_DIRECTORY}")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Monitoramento encerrado.")

if __name__ == '__main__':
    main()