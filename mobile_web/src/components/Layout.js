import React from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';

const Layout = () => {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Main content */}
      <main className="flex-1 pb-16">
        <Outlet />
      </main>
      
      {/* Bottom navigation */}
      <Navigation />
    </div>
  );
};

export default Layout;
