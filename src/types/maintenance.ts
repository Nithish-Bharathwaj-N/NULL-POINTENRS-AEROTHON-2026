// HAL Mission Control - Maintenance & Work Order Contracts
export interface MaintenanceTask {
  id: string;
  engineSerial: string;
  aircraftTail: string;
  taskCode: string;
  title: string;
  category: 'PROPULSION' | 'AVIONICS' | 'STRUCTURE' | 'HYDRAULICS';
  priority: 'ROUTINE' | 'URGENT' | 'AOG';
  rulCountdownHrs: number;
  assignedCrew: string;
  location: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'INSPECTION_REQ' | 'COMPLETED';
  estimatedHours: number;
}

export interface WorkOrder {
  id: string;
  taskIds: string[];
  commanderApproval: boolean;
  issuedDate: string;
  targetCompletionDate: string;
  notes: string;
}
