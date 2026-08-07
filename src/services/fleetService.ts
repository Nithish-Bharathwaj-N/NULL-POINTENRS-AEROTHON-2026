// HAL Mission Control - Fleet Operations API Service
import { FleetMember, SubsystemStage } from '@/types';
import { FLEET_OPERATIONS_LIST, OPERATIONAL_SUBSYSTEM_STAGES } from '@/constants';

export const fleetService = {
  async getFleetList(): Promise<FleetMember[]> {
    return Promise.resolve([...FLEET_OPERATIONS_LIST]);
  },

  async getAircraftByTail(tail: string): Promise<FleetMember | undefined> {
    const ac = FLEET_OPERATIONS_LIST.find((a) => a.tail === tail);
    return Promise.resolve(ac ? { ...ac } : undefined);
  },

  async getSubsystemStages(_tail: string): Promise<SubsystemStage[]> {
    return Promise.resolve([...OPERATIONAL_SUBSYSTEM_STAGES]);
  },
};
