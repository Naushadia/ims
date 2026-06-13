import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Customers from './pages/Customers';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';

const PAGE_TITLES = {
  '/':          'Dashboard',
  '/products':  'Products',
  '/customers': 'Customers',
  '/orders':    'Orders',
};

function AppShell({ title, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-area">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        {children}
      </div>
    </div>
  );
}

import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function App() {
  return (
    <BrowserRouter>
      <ToastContainer position="top-right" autoClose={3000} theme="dark" newestOnTop />
      <Routes>
        <Route path="/" element={
          <AppShell title="Dashboard"><Dashboard /></AppShell>
        } />
        <Route path="/products" element={
          <AppShell title="Products"><Products /></AppShell>
        } />
        <Route path="/customers" element={
          <AppShell title="Customers"><Customers /></AppShell>
        } />
        <Route path="/orders" element={
          <AppShell title="Orders"><Orders /></AppShell>
        } />
        <Route path="/orders/:id" element={
          <AppShell title="Order Detail"><OrderDetail /></AppShell>
        } />
      </Routes>
    </BrowserRouter>
  );
}
