import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { MainLayout } from '@/layouts';
import { WorkstationPage } from '@/pages';
import { useAuthStore } from '@/stores';
import { MissionAccessWorkstation } from '@/features';

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <MainLayout>
        <WorkstationPage />
      </MainLayout>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};
