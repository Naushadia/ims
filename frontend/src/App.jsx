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
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        <Header title={title} />
        {children}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
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
