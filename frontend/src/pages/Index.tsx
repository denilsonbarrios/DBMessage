import React, { useState, useEffect } from 'react';
import { ChartBar, CalendarCheck, Users, MessageSquare } from 'lucide-react';
import DashboardHeader from '@/components/dashboard/DashboardHeader';
import StatisticCard from '@/components/dashboard/StatisticCard';
import InstanceBarChart from '@/components/dashboard/InstanceBarChart';
import SuccessRateChart from '@/components/dashboard/SuccessRateChart';
import InstancesTable from '@/components/dashboard/InstancesTable';
import { DateRange } from 'react-day-picker';

interface InstanceData {
  id: string;
  name: string;
  number: string;
  connectionStatus: string;
  importados: number;
  enviados: number;
  second_sent: number;
}

interface Stats {
  total_appointments: number;
  total_sent: number;
  total_second_sent: number;
  total_failed: number;
  total_pending: number;
  total_instances: number;
  last_processed?: string;
}

interface AppointmentStats {
  instance_id: string;
  importados: number;
  enviados: number;
  second_sent: number;
}

const Index = () => {
  // Definir o dateRange inicial como o mês completo atual (01/04/2025 a 30/04/2025)
  const currentDate = new Date(2025, 3, 26); // 26/04/2025
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
  const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: firstDayOfMonth, // 01/04/2025
    to: lastDayOfMonth,    // 30/04/2025
  });
  const [instances, setInstances] = useState<InstanceData[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_appointments: 0,
    total_sent: 0,
    total_second_sent: 0,
    total_failed: 0,
    total_pending: 0,
    total_instances: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Função para formatar data no formato DD/MM/YYYY
  const formatDate = (date?: Date): string => {
    if (!date) return '';
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  // Buscar dados da API
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Buscar instâncias
      const instancesResponse = await fetch(`http://localhost:8182/instances`);
      if (!instancesResponse.ok) {
        throw new Error(`Erro ao buscar instâncias: ${instancesResponse.statusText}`);
      }
      const instancesData = await instancesResponse.json();
      console.log('Instâncias recebidas:', instancesData);

      // Buscar métricas de agendamentos por instância
      const params = new URLSearchParams();
      if (dateRange?.from) params.append('data_agendamento_start', formatDate(dateRange.from));
      if (dateRange?.to) params.append('data_agendamento_end', formatDate(dateRange.to));
      
      const appointmentsStatsResponse = await fetch(`http://localhost:8182/appointments-stats?${params}`);
      if (!appointmentsStatsResponse.ok) {
        throw new Error(`Erro ao buscar métricas de agendamentos: ${appointmentsStatsResponse.statusText}`);
      }
      const appointmentsStatsData: AppointmentStats[] = await appointmentsStatsResponse.json();
      console.log('Métricas de agendamentos recebidas:', appointmentsStatsData);

      // Combinar instâncias com métricas
      const combinedInstances = instancesData.map((instance: { id: string, name: string, number: string, connectionStatus: string }) => {
        const instanceStats = appointmentsStatsData.find(stats => stats.instance_id === instance.id) || {
          instance_id: instance.id,
          importados: 0,
          enviados: 0,
          second_sent: 0
        };
        return {
          id: instance.id,
          name: instance.name,
          number: instance.number,
          connectionStatus: instance.connectionStatus,
          importados: instanceStats.importados,
          enviados: instanceStats.enviados,
          second_sent: instanceStats.second_sent
        };
      });
      setInstances(combinedInstances);

      // Buscar estatísticas gerais
      const statsResponse = await fetch(`http://localhost:8182/stats?${params}`);
      if (!statsResponse.ok) {
        throw new Error(`Erro ao buscar estatísticas: ${statsResponse.statusText}`);
      }
      const statsData = await statsResponse.json();
      console.log('Estatísticas recebidas:', statsData);
      setStats(statsData);
    } catch (error) {
      console.error('Erro ao buscar dados:', error.message);
      setError(`Erro ao carregar dados: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Buscar dados ao carregar e quando dateRange mudar
  useEffect(() => {
    fetchData();
  }, [dateRange]);

  // Dados para o gráfico (limitar a 8 instâncias)
  const chartData = instances.slice(0, 8);

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 p-6">
        <DashboardHeader 
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
        />
        
        {loading ? (
          <div>Carregando...</div>
        ) : error ? (
          <div className="text-red-500">{error}</div>
        ) : instances.length === 0 ? (
          <div>Nenhuma instância encontrada.</div>
        ) : (
          <>
            {/* Cards de métricas principais */}
            <div className="grid gap-4 grid-cols-1 md:grid-cols-4 mb-6">
              <StatisticCard 
                title="Total de Instâncias" 
                value={stats.total_instances}
                icon={<Users className="h-5 w-5 text-whatsapp-dark" />}
                description="Instâncias monitoradas"
              />
              <StatisticCard 
                title="Agendamentos Importados" 
                value={stats.total_appointments}
                icon={<CalendarCheck className="h-5 w-5 text-whatsapp-dark" />}
                description="Total de importações"
              />
              <StatisticCard 
                title="Mensagens Enviadas" 
                value={stats.total_sent}
                icon={<ChartBar className="h-5 w-5 text-whatsapp" />}
                description="Total de envios com sucesso"
              />
              <StatisticCard 
                title="Segundas Mensagens Enviadas" 
                value={stats.total_second_sent}
                icon={<MessageSquare className="h-5 w-5 text-whatsapp" />}
                description="Lembretes enviados com sucesso"
              />
            </div>
            
            {/* Gráficos */}
            <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-6">
              <InstanceBarChart data={chartData} />
              <SuccessRateChart 
                totalImportados={stats.total_appointments} 
                totalEnviados={stats.total_sent} 
              />
            </div>
            
            {/* Tabela de instâncias */}
            <InstancesTable data={instances} />
          </>
        )}
      </main>
    </div>
  );
};

export default Index;