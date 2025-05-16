import csv
import os
import glob
import sqlite3
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def setup_database():
    conn = sqlite3.connect("whatsapp_messages.db")
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
    conn.commit()
    conn.close()

def parse_csv(csv_file):
    data = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            cleaned_row = {k: (v.strip() if v else '') for k, v in row.items()}
            data.append(cleaned_row)
    return data

def insert_data_to_db(data):
    conn = sqlite3.connect("whatsapp_messages.db")
    cursor = conn.cursor()
    for item in data:
        cursor.execute('''
            INSERT OR IGNORE INTO appointments (
                us_at, razao_social, nome_profissional, cbo_profissional, data_agendamento, codigo,
                usuario, nome_usuario, telefone, telefone_celular, telefone_contato,
                motivo_consulta, horario, inclusao, complemento_unidade, numero_unidade,
                municipio, bairro, logradouro, instance_id, first_message_sent,
                second_message_sent, second_message_date, data_envio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('U.S.At.', ''), item.get('Razão Social da Unidade de Saúde de Aten', ''),
            item.get('Nome do Profissional', ''), item.get('Descrição do CBO Profissional', '').upper(),
            item.get('Data', ''), item.get('Código', ''), item.get('Usuário', ''),
            item.get('Nome do Usuário', ''), item.get('Telefone', ''), item.get('Tel.Celular', ''),
            item.get('Tel.Contato', ''), item.get('Descrição Motivo da Consulta', ''),
            item.get('Horário', '')[:5], item.get('Inclusão', ''),
            item.get('Complemento da Un. de Atendimento', ''), item.get('Número da Unidade de Atendimento', ''),
            item.get('Nome do Município da Un. Atendimento', ''), item.get('Nome do Bairro Un. Atendimento', ''),
            item.get('Nome do Logradouro da Un. Atendimento', ''), None, 'PENDENTE', 'PENDENTE', None, None
        ))
    conn.commit()
    conn.close()

def process_csv_folder(csv_folder='csv'):
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
    csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
    for csv_file in csv_files:
        data = parse_csv(csv_file)
        insert_data_to_db(data)
        os.remove(csv_file)

class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            process_csv_folder()

def main():
    setup_database()
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, "csv/", recursive=False)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
