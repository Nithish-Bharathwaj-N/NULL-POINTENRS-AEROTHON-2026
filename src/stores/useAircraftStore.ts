// HAL Mission Control - Zustand Aircraft & Fleet Store
import { create } from 'zustand';
import { FleetMember } from '@/types';
import { FLEET_OPERATIONS_LIST } from '@/constants';

interface AircraftStoreState {
  fleet: FleetMember[];
  selectedTail: string;
  selectedAircraft: FleetMember;
  setSelectedTail: (tail: string) => void;
  updateAircraftHealth: (tail: string, newHealth: number) => void;
  resetFleet: () => void;
}

export const useAircraftStore = create<AircraftStoreState>((set, get) => ({
  fleet: FLEET_OPERATIONS_LIST,
  selectedTail: 'TJ-103', // Default combat aircraft with active telemetry drift warning
  selectedAircraft: FLEET_OPERATIONS_LIST.find((a) => a.tail === 'TJ-103') || FLEET_OPERATIONS_LIST[0],
  setSelectedTail: (tail) => {
    const ac = get().fleet.find((a) => a.tail === tail) || get().fleet[0];
    set({ selectedTail: ac.tail, selectedAircraft: ac });
  },
  updateAircraftHealth: (tail, newHealth) => {
    set((state) => {
      const updated = state.fleet.map((a) => (a.tail === tail ? { ...a, health: newHealth } : a));
      const active = updated.find((a) => a.tail === state.selectedTail) || updated[0];
      return { fleet: updated, selectedAircraft: active };
    });
  },
  resetFleet: () => {
    const defaultAc = FLEET_OPERATIONS_LIST.find((a) => a.tail === 'TJ-103') || FLEET_OPERATIONS_LIST[0];
    set({ fleet: FLEET_OPERATIONS_LIST, selectedTail: defaultAc.tail, selectedAircraft: defaultAc });
  },
}));
