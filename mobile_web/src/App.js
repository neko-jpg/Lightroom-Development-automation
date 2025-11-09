import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Import pages (to be created in subsequent tasks)
import Dashboard from './pages/Dashboard';
import ApprovalQueue from './pages/ApprovalQueue';
import Sessions from './pages/Sessions';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

// Import layout components
import Layout from './components/Layout';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="approval" element={<ApprovalQueue />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="sessions/:id" element={<Sessions />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}

export default App;
