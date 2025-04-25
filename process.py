import sqlite3
import requests
import os
import glob
import csv
from datetime import datetime
import re

# Configuração do banco de dados SQLite
def setup_database():
    conn = sqlite3.connect('whatsapp_messages.db')
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
            status TEXT DEFAULT 'PENDENTE',
            data_envio TEXT,
            UNIQUE(usuario, inclusao, razao_social)
        )
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados configurado em whatsapp_messages.db.")

# Função para verificar duplicatas no banco
def check_duplicates(usuario, inclusao, razao_social):
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, data_agendamento, horario, nome_usuario
        FROM appointments
        WHERE usuario = ? AND inclusao = ? AND razao_social = ?
    ''', (usuario, inclusao, razao_social))
    result = cursor.fetchone()
    conn.close()
    return result

# Função para parsear o CSV
def parse_csv(csv_file):
    data = []
    print(f"Parseando {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        headers = reader.fieldnames
        print(f"Cabeçalhos encontrados: {headers}")
        
        for row_idx, row in enumerate(reader):
            # Tratar valores que podem não ser strings
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, list):
                    v = ';'.join(str(x) for x in v)
                elif v is None:
                    v = ''
                cleaned_row[k] = v.strip() if isinstance(v, str) else str(v)
            
            # Verificar se a linha é vazia ou sem dados relevantes
            if all(not v for v in cleaned_row.values()):
                print(f"Linha {row_idx + 1} vazia ou sem dados, ignorada.")
                continue
            
            print(f"Linha {row_idx + 1}: {cleaned_row}")
            
            # Renomear chaves para corresponder aos nomes dos campos no banco
            item = {
                'us_at': cleaned_row.get('U.S.At.', ''),
                'razao_social': cleaned_row.get('Razão Social da Unidade de Saúde de Aten', ''),
                'nome_profissional': cleaned_row.get('Nome do Profissional', ''),
                'cbo_profissional': cleaned_row.get('Descrição do CBO Profissional', ''),
                'data_agendamento': cleaned_row.get('Data', ''),
                'codigo': cleaned_row.get('Código', ''),
                'usuario': cleaned_row.get('Usuário', ''),
                'nome_usuario': cleaned_row.get('Nome do Usuário', ''),
                'telefone': cleaned_row.get('Telefone', ''),
                'telefone_celular': cleaned_row.get('Tel.Celular', ''),
                'telefone_contato': cleaned_row.get('Tel.Contato', ''),
                'motivo_consulta': cleaned_row.get('Descrição Motivo da Consulta', ''),
                'horario': cleaned_row.get('Horário', ''),
                'inclusao': cleaned_row.get('Inclusão', ''),
                'complemento_unidade': cleaned_row.get('Complemento da Un. de Atendimento', ''),
                'numero_unidade': cleaned_row.get('Número da Unidade de Atendimento', ''),
                'municipio': cleaned_row.get('Nome do Município da Un. Atendimento', ''),
                'bairro': cleaned_row.get('Nome do Bairro Un. Atendimento', ''),
                'logradouro': cleaned_row.get('Nome do Logradouro da Un. Atendimento', '')
            }
            
            # Adicionar apenas se os campos chave estiverem presentes
            if item['usuario'] and item['inclusao'] and item['razao_social']:
                data.append(item)
            else:
                print(f"Linha {row_idx + 1} ignorada: faltam campos chave (usuario, inclusao, razao_social).")
    
    print(f"Total de registros extraídos: {len(data)}")
    return data

# Função para formatar o número de telefone
def format_phone_number(phone):
    if not phone:
        return None
    # Remover caracteres não numéricos
    digits = re.sub(r'\D', '', phone)
    # Validar se é um número válido (11 dígitos para celular com DDD)
    if len(digits) == 11 and digits != '99999999999':
        return f"+55{digits}"
    return None

# Função para selecionar o melhor número de telefone
def select_phone(telefone_celular, telefone_contato, telefone):
    # Priorizar Tel.Celular, depois Tel.Contato, depois Telefone
    for phone in [telefone_celular, telefone_contato, telefone]:
        formatted = format_phone_number(phone)
        if formatted:
            return formatted
    return None

# Função para inserir dados no banco, evitando duplicatas
def insert_data_to_db(data):
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    
    inserted = 0
    for item in data:
        # Verificar se o registro já existe
        duplicate = check_duplicates(
            item['usuario'], item['inclusao'], item['razao_social']
        )
        if duplicate:
            print(f"Registro duplicado encontrado: ID {duplicate[0]}, "
                  f"Data Agendamento: {duplicate[1]}, Horário: {duplicate[2]}, "
                  f"Nome: {duplicate[3]}")
            continue
        
        cursor.execute('''
            INSERT OR IGNORE INTO appointments (
                us_at, razao_social, nome_profissional, cbo_profissional, data_agendamento, codigo,
                usuario, nome_usuario, telefone, telefone_celular, telefone_contato,
                motivo_consulta, horario, inclusao, complemento_unidade, numero_unidade,
                municipio, bairro, logradouro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['us_at'], item['razao_social'], item['nome_profissional'], item['cbo_profissional'],
            item['data_agendamento'], item['codigo'], item['usuario'],
            item['nome_usuario'], item['telefone'], item['telefone_celular'],
            item['telefone_contato'], item['motivo_consulta'], item['horario'],
            item['inclusao'], item['complemento_unidade'], item['numero_unidade'],
            item['municipio'], item['bairro'], item['logradouro']
        ))
        inserted += cursor.rowcount
    
    conn.commit()
    
    # Verificar o número total de registros no banco
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total_records = cursor.fetchone()[0]
    print(f"Total de registros no banco após inserção: {total_records}")
    
    # Listar os primeiros 5 registros para validação
    cursor.execute('SELECT id, usuario, inclusao, razao_social, nome_usuario FROM appointments LIMIT 5')
    sample_records = cursor.fetchall()
    print("Amostra de registros inseridos:")
    for record in sample_records:
        print(f"ID: {record[0]}, Usuário: {record[1]}, Inclusão: {record[2]}, Razão Social: {record[3]}, Nome: {record[4]}")
    
    conn.close()
    print(f"{inserted} registros inseridos no banco.")
    return inserted

# Função para enviar mensagens via API
def send_whatsapp_message():
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, nome_usuario, telefone_celular, telefone_contato, telefone, data_agendamento,
               horario, motivo_consulta, municipio, bairro, logradouro, razao_social,
               nome_profissional, cbo_profissional, numero_unidade
        FROM appointments WHERE status = 'PENDENTE'
    ''')
    appointments = cursor.fetchall()
    
    sent = 0
    for appt in appointments:
        appt_id, nome, telefone_celular, telefone_contato, telefone, data, horario, motivo, municipio, bairro, logradouro, razao_social, profissional, especialidade, numero_unidade = appt
        
        # Selecionar o melhor número de telefone
        formatted_phone = select_phone(telefone_celular, telefone_contato, telefone)
        if not formatted_phone:
            cursor.execute('''
                UPDATE appointments
                SET status = 'FALHA', data_envio = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
            print(f"Telefone inválido para {nome}: {telefone_celular}, {telefone_contato}, {telefone}")
            conn.commit()
            continue
        
        # Aplicar tratamentos aos campos
        especialidade = especialidade.upper()  # Todas as letras maiúsculas
        municipio = municipio.capitalize()     # Primeira letra maiúscula, resto minúsculo
        horario = horario[:5]                 # Remover os segundos (HH:MM:SS → HH:MM)
        
        # Formatando a mensagem
        mensagem = (
            f"Ola, {nome}, Sou a Assistente Virtual de Agendamentos da Secretaria Municipal de Saude de Bebedouro.\n\n"
            f"Estamos entrando em contato para confirmar o seu agendamento do dia {data} às {horario} com o {profissional}, {especialidade}.\n\n"
            f"Podemos confirmar sua presença ?\n\n"
            f"LOCAL DE ATENDIMENTO: {razao_social}, Rua {logradouro} - {numero_unidade}, {bairro}, {municipio}"
        )
        
        payload = {
            "number": formatted_phone,
            "text": mensagem,
            "delay": 5000
        }
        
        headers = {
            'apikey': '3A0C6E4B89B9-4625-8FAB-487529276421'
        }
        
        try:
            response = requests.post('http://localhost:8081/message/sendText/TesteWebApp', json=payload, headers=headers)
            print(f"Resposta da API para {formatted_phone}: {response.status_code} - {response.text}")  # Logar código e resposta
            if response.status_code == 201:
                cursor.execute('''
                    UPDATE appointments
                    SET status = 'ENVIADO', data_envio = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appt_id))
                print(f"Mensagem para {formatted_phone} enviada com sucesso!")
                sent += 1
            else:
                cursor.execute('''
                    UPDATE appointments
                    SET status = 'FALHA'
                    WHERE id = ?
                ''', (appt_id,))
                print(f"Falha ao enviar mensagem para {formatted_phone}: {response.status_code} - {response.text}")
        except Exception as e:
            cursor.execute('''
                UPDATE appointments
                SET status = 'FALHA'
                WHERE id = ?
            ''', (appt_id,))
            print(f"Erro ao enviar mensagem para {formatted_phone}: {str(e)}")
        
        conn.commit()
    
    conn.close()
    print(f"{sent} mensagens enviadas.")
    return sent

# Função para processar todos os CSVs na pasta
def process_csv_folder(csv_folder='csv'):
    # Criar pasta se não existir
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
    
    # Encontrar todos os arquivos CSV
    csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
    
    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado em {csv_folder}")
        return
    
    for csv_file in csv_files:
        print(f"Processando {csv_file}...")
        try:
            # Parsear CSV
            report_data = parse_csv(csv_file)
            
            # Inserir dados no banco
            inserted = insert_data_to_db(report_data)
            
            # Enviar mensagens
            sent = send_whatsapp_message()
            
            # Apagar o arquivo após processamento bem-sucedido
            if inserted > 0 or sent > 0:
                os.remove(csv_file)
                print(f"Arquivo {csv_file} processado e removido com sucesso.")
            else:
                print(f"Nenhum dado novo inserido ou mensagem enviada. Arquivo {csv_file} mantido.")
        
        except Exception as e:
            print(f"Erro ao processar {csv_file}: {str(e)}")
            # Arquivo é mantido em caso de erro para depuração

# Função principal
def main():
    # Configurar banco de dados
    setup_database()
    
    # Processar todos os CSVs na pasta
    process_csv_folder()
    
    print("Processamento concluído!")

if __name__ == '__main__':
    main()