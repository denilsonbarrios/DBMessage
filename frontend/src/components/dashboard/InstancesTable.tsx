import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface InstanceData {
  id: string;
  name: string;
  number: string;
  connectionStatus: string;
  importados: number;
  enviados: number;
  second_sent: number;
}

interface InstancesTableProps {
  data: InstanceData[];
}

const InstancesTable = ({ data }: InstancesTableProps) => {
  return (
    <Card className="col-span-1 md:col-span-3">
      <CardHeader>
        <CardTitle>Detalhes por Instância</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Instância</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Importados</TableHead>
              <TableHead className="text-right">Enviados</TableHead>
              <TableHead className="text-right">Segundas Enviadas</TableHead>
              <TableHead className="text-right">Taxa de Sucesso</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((instance) => {
              const successRate = instance.importados > 0 
                ? ((instance.enviados / instance.importados) * 100).toFixed(1) 
                : '0.0';
              const status = instance.connectionStatus === 'open' ? 'Online' : 'Offline';
                
              return (
                <TableRow key={instance.id}>
                  <TableCell className="font-medium">{instance.name}</TableCell>
                  <TableCell>{status}</TableCell>
                  <TableCell className="text-right">{instance.importados.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{instance.enviados.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{instance.second_sent.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{successRate}%</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default InstancesTable;