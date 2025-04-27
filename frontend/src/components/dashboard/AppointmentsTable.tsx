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

interface Appointment {
  id: number;
  nome_usuario: string;
  data_agendamento: string;
  horario: string;
  nome_profissional: string;
  cbo_profissional: string;
  status: string;
  data_envio?: string;
}

interface AppointmentsTableProps {
  data: Appointment[];
}

const AppointmentsTable: React.FC<AppointmentsTableProps> = ({ data }) => {
  return (
    <Card className="col-span-1 md:col-span-3 mt-6">
      <CardHeader>
        <CardTitle>Detalhes dos Agendamentos</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Usuário</TableHead>
              <TableHead>Data</TableHead>
              <TableHead>Horário</TableHead>
              <TableHead>Profissional</TableHead>
              <TableHead>Especialidade</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Data de Envio</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((appt) => (
              <TableRow key={appt.id}>
                <TableCell>{appt.id}</TableCell>
                <TableCell>{appt.nome_usuario}</TableCell>
                <TableCell>{appt.data_agendamento}</TableCell>
                <TableCell>{appt.horario}</TableCell>
                <TableCell>{appt.nome_profissional}</TableCell>
                <TableCell>{appt.cbo_profissional}</TableCell>
                <TableCell>{appt.status}</TableCell>
                <TableCell>{appt.data_envio || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default AppointmentsTable;