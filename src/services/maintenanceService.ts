// HAL Mission Control - Maintenance Work Order & Report Generator Service
import { MaintenanceTask } from '@/types';
import { OPERATIONAL_MAINTENANCE_TASKS } from '@/constants';

export const maintenanceService = {
  async getWorkOrders(squadronFilter?: string): Promise<MaintenanceTask[]> {
    if (squadronFilter) {
      return Promise.resolve(OPERATIONAL_MAINTENANCE_TASKS.filter((t) => t.location.includes(squadronFilter) || true));
    }
    return Promise.resolve([...OPERATIONAL_MAINTENANCE_TASKS]);
  },

  async updateTaskStatus(_taskId: string, _status: MaintenanceTask['status']): Promise<boolean> {
    return Promise.resolve(true);
  },
};

export const reportService = {
  async generateAirworthinessReport(engineSerial: string, format: 'PDF' | 'DOCX'): Promise<{ url: string; filename: string }> {
    return Promise.resolve({
      url: 'blob:https://hal.res.in/reports/airworthiness-cert-88219.pdf',
      filename: `HAL_LCA_Tejas_Airworthiness_Cert_${engineSerial.replace(/\s+/g, '_')}.${format.toLowerCase()}`,
    });
  },
};
