import React from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface InstanceData {
  name: string;
  importados: number;
  enviados: number;
  second_sent: number;
}

interface InstanceBarChartProps {
  data: InstanceData[];
}

const InstanceBarChart = ({ data }: InstanceBarChartProps) => {
  return (
    <Card className="col-span-1 md:col-span-2">
      <CardHeader>
        <CardTitle>Instâncias - Importados vs Enviados</CardTitle>
      </CardHeader>
      <CardContent className="h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip 
              formatter={(value) => [`${value} mensagens`, '']}
              labelFormatter={(label) => `Instância: ${label}`}
            />
            <Legend />
            <Bar 
              dataKey="importados" 
              fill="#128C7E" 
              name="Importados" 
              radius={[3, 3, 0, 0]} 
            />
            <Bar 
              dataKey="enviados" 
              fill="#25D366" 
              name="Enviados" 
              radius={[3, 3, 0, 0]} 
            />
            <Bar 
              dataKey="second_sent" 
              fill="#075E54" 
              name="Segundas Enviadas" 
              radius={[3, 3, 0, 0]} 
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default InstanceBarChart;