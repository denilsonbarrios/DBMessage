
import React from 'react';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SuccessRateChartProps {
  totalImportados: number;
  totalEnviados: number;
}

const SuccessRateChart = ({ totalImportados, totalEnviados }: SuccessRateChartProps) => {
  const data = [
    { name: 'Enviados', value: totalEnviados, color: '#25D366' },
    { name: 'Pendentes', value: Math.max(0, totalImportados - totalEnviados), color: '#ECE5DD' },
  ];

  const successRate = totalImportados > 0 
    ? Math.round((totalEnviados / totalImportados) * 100) 
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Taxa de Sucesso</CardTitle>
        <CardDescription>Percentual de mensagens enviadas com sucesso</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="h-[180px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [`${value} mensagens`, name]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 text-center">
          <span className="text-3xl font-bold">
            {successRate}%
          </span>
          <p className={cn(
            "text-sm mt-1",
            successRate > 90 ? "text-green-600" : 
            successRate > 70 ? "text-yellow-600" : "text-red-600"
          )}>
            {successRate > 90 ? "Excelente" : 
             successRate > 70 ? "Bom" : "Precisa melhorar"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default SuccessRateChart;
