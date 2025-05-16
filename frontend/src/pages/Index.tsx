import React, { useState, useEffect } from 'react';
import { ChartBar, CalendarCheck, Users, MessageSquare, Plus } from 'lucide-react';
import DashboardHeader from '@/components/dashboard/DashboardHeader';
import StatisticCard from '@/components/dashboard/StatisticCard';
import InstanceBarChart from '@/components/dashboard/InstanceBarChart';
import SuccessRateChart from '@/components/dashboard/SuccessRateChart';
import InstancesTable from '@/components/dashboard/InstancesTable';
import { DateRange } from 'react-day-picker';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
  const currentDate = new Date(2025, 3, 26);
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
  const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: firstDayOfMonth,
    to: lastDayOfMonth,
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

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    us_at: '',
    instance_id: '',
    instance_name: '',
    token: ''
  });
  const [formError, setFormError] = useState<string | null>(null);

  const formatDate = (date?: Date): string => {
    if (!date) return '';
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const instancesResponse = await fetch(`http://localhost:8182/instances`);
      if (!instancesResponse.ok) {
        throw new Error(`Erro ao buscar instâncias: ${instancesResponse.statusText}`);
      }
      const instancesData = await instancesResponse.json();
      console.log('Instâncias recebidas:', instancesData);

      const params = new URLSearchParams();
      if (dateRange?.from) params.append('data_agendamento_start', formatDate(dateRange.from));
      if (dateRange?.to) params.append('data_agendamento_end', formatDate(dateRange.to));
      
      const appointmentsStatsResponse = await fetch(`http://localhost:8182/appointments-stats?${params}`);
      if (!appointmentsStatsResponse.ok) {
        throw new Error(`Erro ao buscar métricas de agendamentos: ${appointmentsStatsResponse.statusText}`);
      }
      const appointmentsStatsData: AppointmentStats[] = await appointmentsStatsResponse.json();
      console.log('Métricas de agendamentos recebidas:', appointmentsStatsData);

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

  // Atualizar dados inicialmente e a cada 10 segundos
  useEffect(() => {
    fetchData(); // Chamada inicial

    const intervalId = setInterval(() => {
      console.log('Atualizando dados do dashboard...');
      fetchData();
    }, 100000); // 10 segundos

    // Limpar o intervalo quando o componente for desmontado
    return () => clearInterval(intervalId);
  }, [dateRange]);

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    try {
      const response = await fetch('http://localhost:8182/instance-mapping', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao adicionar instância');
      }

      const result = await response.json();
      console.log('Instância adicionada:', result);
      setIsDialogOpen(false);
      setFormData({ us_at: '', instance_id: '', instance_name: '', token: '' });
      fetchData();
    } catch (error) {
      console.error('Erro ao adicionar instância:', error.message);
      setFormError(error.message);
    }
  };

  const chartData = instances.slice(0, 8);

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 p-6">
        <div className="flex justify-between items-center mb-6">
          <DashboardHeader 
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
          />
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Instância
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Adicionar Nova Instância</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleFormSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="us_at">Unidade de Saúde (us_at)</Label>
                  <Input
                    id="us_at"
                    name="us_at"
                    value={formData.us_at}
                    onChange={handleFormChange}
                    placeholder="Ex.: 2"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="instance_id">ID da Instância</Label>
                  <Input
                    id="instance_id"
                    name="instance_id"
                    value={formData.instance_id}
                    onChange={handleFormChange}
                    placeholder="Ex.: 9cb57386-120e-40fb-b112-6c901fa6e00a"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="instance_name">Nome da Instância</Label>
                  <Input
                    id="instance_name"
                    name="instance_name"
                    value={formData.instance_name}
                    onChange={handleFormChange}
                    placeholder="Ex.: TesteWebApp"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="token">Token (API Key)</Label>
                  <Input
                    id="token"
                    name="token"
                    value={formData.token}
                    onChange={handleFormChange}
                    placeholder="Ex.: 3A0C6E4B89B9-4625-8FAB-487529276421"
                    required
                  />
                </div>
                {formError && <p className="text-red-500">{formError}</p>}
                <Button type="submit">Adicionar</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        
        {loading ? (
          <div>Carregando...</div>
        ) : error ? (
          <div className="text-red-500">{error}</div>
        ) : instances.length === 0 ? (
          <div>Nenhuma instância encontrada.</div>
        ) : (
          <>
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
            
            <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-6">
              <InstanceBarChart data={chartData} />
              <SuccessRateChart 
                totalImportados={stats.total_appointments} 
                totalEnviados={stats.total_sent} 
              />
            </div>
            
            <InstancesTable data={instances} />
          </>
        )}
      </main>
    </div>
  );
};

export default Index;