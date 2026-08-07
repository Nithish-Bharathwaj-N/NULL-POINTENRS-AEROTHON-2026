// HAL Mission Control - Live Telemetry Service
import { TelemetrySensor, TransducerChannel } from '@/types';
import { useMissionStore } from '@/stores/useMissionStore';

export const telemetryService = {
  async getLatestSensorData(engineId: string): Promise<TelemetrySensor> {
    console.debug(`[TelemetryService] Fetching live snapshot for engine ${engineId}`);
    return Promise.resolve({ ...useMissionStore.getState().telemetry });
  },

  async getTransducerChannels(engineId: string): Promise<TransducerChannel[]> {
    console.debug(`[TelemetryService] Fetching live channels for engine ${engineId}`);
    const tel = useMissionStore.getState().telemetry;
    const t3C = Number((tel.t3Kelvin - 273.15).toFixed(1));
    const t4C = Number((tel.t4Kelvin - 273.15).toFixed(1));

    return Promise.resolve([
      {
        id: 'T3-CH1',
        name: 'T3 High-Press Compressor Discharge Temp',
        sensorRef: 'hpc',
        channel: 'ARINC-429 Ch 1',
        unit: '°C',
        current: t3C,
        expected: 450.0,
        delta: Number((t3C - 450.0).toFixed(1)),
        minVal: 400,
        maxVal: 650,
        status: t3C > 580 ? 'CRITICAL' : t3C > 520 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0342 (Octal)',
      },
      {
        id: 'T4-CH1',
        name: 'T4 Turbine Inlet Temperature (EGT)',
        sensorRef: 'combustor',
        channel: 'ARINC-429 Ch 2',
        unit: '°C',
        current: t4C,
        expected: 1412.0,
        delta: Number((t4C - 1412.0).toFixed(1)),
        minVal: 1200,
        maxVal: 1550,
        status: t4C > 1480 ? 'CRITICAL' : t4C > 1430 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0344 (Octal)',
      },
      {
        id: 'P2-CH1',
        name: 'P2 Fan Discharge Pressure',
        sensorRef: 'lpc',
        channel: 'ARINC-429 Ch 3',
        unit: 'Bar',
        current: tel.p2Bar,
        expected: 2.38,
        delta: Number((tel.p2Bar - 2.38).toFixed(2)),
        minVal: 1.5,
        maxVal: 3.5,
        status: tel.p2Bar > 3.2 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0212 (Octal)',
      },
      {
        id: 'P3-CH1',
        name: 'P3 HPC Discharge Pressure',
        sensorRef: 'hpc',
        channel: 'ARINC-429 Ch 4',
        unit: 'Bar',
        current: tel.p3Bar,
        expected: 24.1,
        delta: Number((tel.p3Bar - 24.1).toFixed(1)),
        minVal: 18.0,
        maxVal: 30.0,
        status: tel.p3Bar > 28.0 ? 'CRITICAL' : tel.p3Bar > 26.0 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0214 (Octal)',
      },
      {
        id: 'VIB-N1',
        name: 'N1 Low-Pressure Spool RMS Vibration',
        sensorRef: 'fan',
        channel: 'Piezo-Transducer A',
        unit: 'G',
        current: tel.vibrationG,
        expected: 0.80,
        delta: Number((tel.vibrationG - 0.80).toFixed(2)),
        minVal: 0.1,
        maxVal: 2.5,
        status: tel.vibrationG > 2.0 ? 'CRITICAL' : tel.vibrationG > 1.4 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0112 (Octal)',
      },
      {
        id: 'VIB-N2',
        name: 'N2 High-Pressure Spool RMS Vibration',
        sensorRef: 'hpt',
        channel: 'Piezo-Transducer B',
        unit: 'G',
        current: Number((tel.vibrationG * 1.15).toFixed(2)),
        expected: 1.10,
        delta: Number((tel.vibrationG * 1.15 - 1.10).toFixed(2)),
        minVal: 0.1,
        maxVal: 2.5,
        status: tel.vibrationG * 1.15 > 2.0 ? 'CRITICAL' : tel.vibrationG * 1.15 > 1.5 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0114 (Octal)',
      },
      {
        id: 'OIL-P1',
        name: 'Main Engine Bearing Oil Pressure',
        sensorRef: 'lpt',
        channel: 'Hydro-Transducer C',
        unit: 'PSI',
        current: tel.oilPressurePsi,
        expected: 68.0,
        delta: Number((tel.oilPressurePsi - 68.0).toFixed(1)),
        minVal: 40.0,
        maxVal: 90.0,
        status: tel.oilPressurePsi < 45.0 ? 'CRITICAL' : tel.oilPressurePsi < 55.0 ? 'WARNING' : 'NOMINAL',
        arinc429Word: '0412 (Octal)',
      },
    ]);
  },
};
