
import React, { useState } from 'react';
import { ChartBar, CalendarCheck, Users } from 'lucide-react';
import DashboardHeader from '@/components/dashboard/DashboardHeader';
import StatisticCard from '@/components/dashboard/StatisticCard';
import InstanceBarChart from '@/components/dashboard/InstanceBarChart';
import SuccessRateChart from '@/components/dashboard/SuccessRateChart';
import InstancesTable from '@/components/dashboard/InstancesTable';
import { generateMockInstances, calculateTotals } from '@/data/mockData';
import { DateRange } from 'react-day-picker';

const Index = () => {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: new Date(2025, 3, 1), // April 1, 2025
    to: new Date(2025, 3, 25),  // April 25, 2025
  });
  const [selectedMonth, setSelectedMonth] = useState("3"); // April (0-based index)
  const [instances] = useState(generateMockInstances(20));
  
  const { totalImportados, totalEnviados } = calculateTotals(instances);
  const instancesCount = instances.length;

  // Limita a exibição no gráfico para não ficar muito poluído
  const chartData = instances.slice(0, 8);

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 p-6">
        <DashboardHeader 
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          selectedMonth={selectedMonth}
          onMonthChange={setSelectedMonth}
        />
        
        {/* Cards de métricas principais */}
        <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-6">
          <StatisticCard 
            title="Total de Instâncias" 
            value={instancesCount}
            icon={<Users className="h-5 w-5 text-whatsapp-dark" />}
            description="Instâncias monitoradas"
          />
          <StatisticCard 
            title="Agendamentos Importados" 
            value={totalImportados}
            icon={<CalendarCheck className="h-5 w-5 text-whatsapp-dark" />}
            description="Total de importações"
          />
          <StatisticCard 
            title="Mensagens Enviadas" 
            value={totalEnviados}
            icon={<ChartBar className="h-5 w-5 text-whatsapp" />}
            description="Total de envios com sucesso"
          />
        </div>
        
        {/* Gráficos */}
        <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-6">
          <InstanceBarChart data={chartData} />
          <SuccessRateChart 
            totalImportados={totalImportados} 
            totalEnviados={totalEnviados} 
          />
        </div>
        
        {/* Tabela detalhada */}
        <InstancesTable data={instances} />
      </main>
    </div>
  );
};

export default Index;

