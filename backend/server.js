const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const axios = require('axios');

const app = express();
const port = 8182;

// Configurar CORS para permitir requisições do frontend
app.use(cors());
app.use(express.json());

// Conexão com o banco SQLite na pasta raiz
const db = new sqlite3.Database('../whatsapp_messages.db', (err) => {
  if (err) {
    console.error('Erro ao conectar ao banco:', err.message);
  } else {
    console.log('Conectado ao banco whatsapp_messages.db na pasta raiz');
  }
});

// Configuração do axios para a API WhatsApp (HTTP)
const whatsappApi = axios.create({
  baseURL: 'http://localhost:8081',
  headers: {
    'apikey': '3A0C6E4B89B9-4625-8FAB-487529276421'
  }
});

// Endpoint para listar instâncias
app.get('/instances', async (req, res) => {
  console.log('Requisição /instances');
  
  try {
    // Buscar instâncias da API WhatsApp
    let response;
    try {
      response = await whatsappApi.get('/instance/fetchInstances');
      console.log('Resposta de /instance/fetchInstances:', JSON.stringify(response.data, null, 2));
    } catch (apiError) {
      console.error('Erro ao chamar /instance/fetchInstances:', apiError.message, apiError.stack);
      if (apiError.response) {
        console.error('Resposta da API:', apiError.response.status, apiError.response.data);
      }
      throw new Error(`Falha na API WhatsApp: ${apiError.message}`);
    }
    
    if (!Array.isArray(response.data)) {
      console.error('Resposta inválida: não é um array');
      throw new Error('Resposta de instâncias não é um array');
    }
    
    // Mapear instâncias
    const instances = response.data.map(instance => ({
      id: instance.id || 'unknown',
      name: instance.name || instance.id || 'Desconhecido',
      number: instance.number || '',
      connectionStatus: instance.connectionStatus || 'unknown'
    }));
    
    console.log('Instâncias retornadas:', JSON.stringify(instances, null, 2));
    res.json(instances);
  } catch (error) {
    console.error('Erro ao buscar instâncias:', error.message, error.stack);
    res.status(500).json({ error: `Erro ao buscar instâncias: ${error.message}` });
  }
});

// Endpoint para métricas de agendamentos por instância
app.get('/appointments-stats', async (req, res) => {
  const { data_agendamento_start, data_agendamento_end } = req.query;
  console.log('Requisição /appointments-stats com filtros:', { data_agendamento_start, data_agendamento_end });
  
  try {
    // Construir a cláusula WHERE
    const conditions = [];
    const params = [];
    
    if (data_agendamento_start) {
      conditions.push('data_agendamento >= ?');
      params.push(data_agendamento_start);
    }
    if (data_agendamento_end) {
      conditions.push('data_agendamento <= ?');
      params.push(data_agendamento_end);
    }
    
    const whereClause = conditions.length > 0 ? ` WHERE ${conditions.join(' AND ')}` : '';
    
    // Consulta para métricas por instance_id
    const query = `
      SELECT 
        instance_id,
        COUNT(*) as importados,
        SUM(CASE WHEN first_message_sent = 'ENVIADO' OR second_message_sent = 'ENVIADO' THEN 1 ELSE 0 END) as enviados,
        SUM(CASE WHEN second_message_sent = 'ENVIADO' THEN 1 ELSE 0 END) as second_sent
      FROM appointments
      ${whereClause}
      GROUP BY instance_id
    `;
    
    const stats = await new Promise((resolve, reject) => {
      db.all(query, params, (err, rows) => {
        if (err) {
          console.error('Erro ao consultar métricas por instância:', err.message);
          reject(err);
        } else {
          resolve(rows.map(row => ({
            instance_id: row.instance_id,
            importados: row.importados,
            enviados: row.enviados,
            second_sent: row.second_sent
          })));
        }
      });
    });
    
    console.log('Métricas por instância retornadas:', JSON.stringify(stats, null, 2));
    res.json(stats);
  } catch (error) {
    console.error('Erro ao buscar métricas de agendamentos:', error.message, error.stack);
    res.status(500).json({ error: `Erro ao buscar métricas: ${error.message}` });
  }
});

// Endpoint para estatísticas gerais
app.get('/stats', async (req, res) => {
  const { data_agendamento_start, data_agendamento_end } = req.query;
  console.log('Requisição /stats com filtros:', { data_agendamento_start, data_agendamento_end });
  
  const conditions = [];
  const params = [];
  
  if (data_agendamento_start) {
    conditions.push('data_agendamento >= ?');
    params.push(data_agendamento_start);
  }
  if (data_agendamento_end) {
    conditions.push('data_agendamento <= ?');
    params.push(data_agendamento_end);
  }
  
  const whereClause = conditions.length > 0 ? ` WHERE ${conditions.join(' AND ')}` : '';
  
  const queries = [
    { sql: `SELECT COUNT(*) as total FROM appointments${whereClause}`, key: 'total_appointments' },
    { sql: `SELECT COUNT(*) as total FROM appointments${whereClause ? `${whereClause} AND` : ' WHERE'} (first_message_sent = 'ENVIADO' OR second_message_sent = 'ENVIADO')`, key: 'total_sent' },
    { sql: `SELECT COUNT(*) as total FROM appointments${whereClause ? `${whereClause} AND` : ' WHERE'} second_message_sent = 'ENVIADO'`, key: 'total_second_sent' },
    { sql: `SELECT COUNT(*) as total FROM appointments${whereClause ? `${whereClause} AND` : ' WHERE'} (first_message_sent = 'FALHA' OR second_message_sent = 'FALHA')`, key: 'total_failed' },
    { sql: `SELECT COUNT(*) as total FROM appointments${whereClause ? `${whereClause} AND` : ' WHERE'} (first_message_sent = 'PENDENTE' AND second_message_sent = 'PENDENTE')`, key: 'total_pending' },
    { sql: `SELECT MAX(data_envio) as last_processed FROM appointments${whereClause}`, key: 'last_processed' }
  ];
  
  const stats = {};
  let completedQueries = 0;
  
  // Buscar instâncias
  try {
    const instancesResponse = await whatsappApi.get('/instance/fetchInstances');
    stats.total_instances = Array.isArray(instancesResponse.data) ? instancesResponse.data.length : 0;
    console.log('Total de instâncias:', stats.total_instances);
  } catch (error) {
    console.error('Erro ao buscar instâncias para /stats:', error.message, error.stack);
    stats.total_instances = 0;
  }
  
  queries.forEach(({ sql, key }) => {
    db.get(sql, params, (err, row) => {
      if (err) {
        console.error(`Erro ao executar ${key}:`, err.message);
        stats[key] = 0;
      } else {
        stats[key] = key === 'last_processed' ? row.last_processed : row.total;
      }
      
      completedQueries++;
      if (completedQueries === queries.length) {
        console.log('Estatísticas retornadas:', JSON.stringify(stats, null, 2));
        res.json(stats);
      }
    });
  });
});

// Iniciar o servidor
app.listen(port, () => {
  console.log(`Servidor rodando em http://localhost:${port}`);
});