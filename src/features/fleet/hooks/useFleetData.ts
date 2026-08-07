// HAL Mission Control - Fleet Feature Hooks
import { useState, useMemo } from 'react';
import { useAircraftStore } from '@/stores';

export const useFleetData = () => {
  const { fleet, selectedTail, setSelectedTail, selectedAircraft } = useAircraftStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [squadronFilter, setSquadronFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [activeTab, setActiveTab] = useState<'matrix' | 'list'>('matrix');

  const filteredFleet = useMemo(() => {
    return fleet.filter((ac) => {
      const matchSearch =
        ac.tail.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ac.pilot.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ac.location.toLowerCase().includes(searchQuery.toLowerCase());
      const matchSqn = squadronFilter === 'ALL' || ac.squadron.includes(squadronFilter);
      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'AIRBORNE' && ac.status.includes('Combat')) ||
        (statusFilter === 'QRA' && ac.status.includes('Standby')) ||
        (statusFilter === 'GROUNDED' && ac.status.includes('Grounded'));
      return matchSearch && matchSqn && matchStatus;
    });
  }, [fleet, searchQuery, squadronFilter, statusFilter]);

  const fleetMetrics = useMemo(() => {
    const total = fleet.length;
    const airborne = fleet.filter((a) => a.status.includes('Combat')).length;
    const qra = fleet.filter((a) => a.status.includes('Standby')).length;
    const grounded = fleet.filter((a) => a.status.includes('Grounded')).length;
    const avgHealth = Math.round(fleet.reduce((acc, a) => acc + a.health, 0) / (total || 1));
    return [
      { label: 'Total IAF Fleet', val: `${total} A/C`, sub: '3 Operational Squadrons', status: 'NOMINAL' },
      { label: 'Airborne / Sorties', val: `${airborne} A/C`, sub: 'Active Combat & Test Patrols', status: 'ACTIVE' },
      { label: 'Armed Standby (QRA)', val: `${qra} A/C`, sub: '2-Min Intercept Readiness', status: 'WARNING' },
      { label: 'Grounded / Maintenance', val: `${grounded} A/C`, sub: 'HAL Overhaul & Borescope Bay', status: 'CRITICAL' },
      { label: 'Fleet Health Index', val: `${avgHealth}%`, sub: 'AeroNet-v4 Weighted Avg', status: avgHealth >= 85 ? 'NOMINAL' : 'WARNING' },
      { label: 'IAF Operational Readiness', val: `${Math.round(((airborne + qra) / total) * 100)}%`, sub: 'Target: >80% Mission Capable', status: 'NOMINAL' },
    ];
  }, [fleet]);

  return {
    fleet,
    filteredFleet,
    selectedTail,
    setSelectedTail,
    selectedAircraft,
    searchQuery,
    setSearchQuery,
    squadronFilter,
    setSquadronFilter,
    statusFilter,
    setStatusFilter,
    activeTab,
    setActiveTab,
    fleetMetrics,
  };
};
