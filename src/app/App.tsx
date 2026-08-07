import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from './router';
import { missionPlaybackEngine } from '@/services/missionPlaybackEngine';
import { unityBridgeService } from '@/services';

// Create a client for TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 30000,
      retry: 1,
    },
  },
});

export const App: React.FC = React.memo(() => {
  useEffect(() => {
    // Initialize Wasm CAD Bridge Hydration
    unityBridgeService.setHydrated(true);

    // Boot the single Mission Playback Engine — the heartbeat of the entire platform.
    // All workstations subscribe to ONE master clock driven by the HAL dataset.
    missionPlaybackEngine.start();

    return () => {
      missionPlaybackEngine.stop();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
    </QueryClientProvider>
  );
});
App.displayName = 'App';
export default App;
