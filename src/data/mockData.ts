
export interface InstanceData {
  id: string;
  name: string;
  importados: number;
  enviados: number;
}

// Gera instâncias com números aleatórios para demonstração
export const generateMockInstances = (count: number = 20) => {
  const instances: InstanceData[] = [];

  for (let i = 1; i <= count; i++) {
    const importados = Math.floor(Math.random() * 1000) + 100;
    const enviados = Math.floor(Math.random() * importados);
    
    instances.push({
      id: `inst-${i}`,
      name: `Instância ${i}`,
      importados,
      enviados
    });
  }

  return instances;
};

// Calcula totais a partir das instâncias
export const calculateTotals = (instances: InstanceData[]) => {
  return instances.reduce(
    (acc, instance) => {
      acc.totalImportados += instance.importados;
      acc.totalEnviados += instance.enviados;
      return acc;
    },
    { totalImportados: 0, totalEnviados: 0 }
  );
};
