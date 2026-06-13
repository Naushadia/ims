import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProducts } from '../api/products';
import { getCustomers } from '../api/customers';
import { getOrders } from '../api/orders';

export default function Header({ title, onMenuClick }) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const dropdownRef = useRef(null);

  // Load search data on focus
  useEffect(() => {
    if (isFocused && products.length === 0) {
      getProducts().then(res => setProducts(res.data || [])).catch(() => {});
      getCustomers().then(res => setCustomers(res.data || [])).catch(() => {});
      getOrders().then(res => setOrders(res.data || [])).catch(() => {});
    }
  }, [isFocused, products.length]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsFocused(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const q = searchQuery.toLowerCase().trim();
  
  const filteredProducts = q
    ? products.filter(p => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)).slice(0, 4)
    : [];

  const filteredCustomers = q
    ? customers.filter(c => c.full_name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q)).slice(0, 4)
    : [];

  const filteredOrders = q
    ? orders.filter(o => 
        String(o.id).includes(q) || 
        o.customer?.full_name.toLowerCase().includes(q) ||
        o.status.toLowerCase().includes(q)
      ).slice(0, 4)
    : [];

  const hasResults = filteredProducts.length > 0 || filteredCustomers.length > 0 || filteredOrders.length > 0;

  const handleItemClick = (path) => {
    navigate(path);
    setSearchQuery('');
    setIsFocused(false);
  };

  return (
    <header className="top-header">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <button className="mobile-hamburger" onClick={onMenuClick} title="Open Navigation">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 className="header-title">{title}</h1>
      </div>

      <div className="header-actions">
        <div className="header-search" ref={dropdownRef}>
          <svg className="header-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input 
            type="text" 
            placeholder="Quick search..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
          />

          {isFocused && searchQuery.trim() !== '' && (
            <div className="search-results-dropdown">
              {filteredProducts.length > 0 && (
                <div>
                  <div className="search-section-title">Products</div>
                  {filteredProducts.map(p => (
                    <div key={p.id} className="search-result-item" onClick={() => handleItemClick('/products')}>
                      <span className="search-result-primary">{p.name}</span>
                      <span className="search-result-secondary">{p.sku} · ₹{parseFloat(p.price).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}

              {filteredCustomers.length > 0 && (
                <div>
                  <div className="search-section-title">Customers</div>
                  {filteredCustomers.map(c => (
                    <div key={c.id} className="search-result-item" onClick={() => handleItemClick('/customers')}>
                      <span className="search-result-primary">{c.full_name}</span>
                      <span className="search-result-secondary">{c.email}</span>
                    </div>
                  ))}
                </div>
              )}

              {filteredOrders.length > 0 && (
                <div>
                  <div className="search-section-title">Orders</div>
                  {filteredOrders.map(o => (
                    <div key={o.id} className="search-result-item" onClick={() => handleItemClick(`/orders/${o.id}`)}>
                      <span className="search-result-primary">Order #{String(o.id).padStart(4, '0')}</span>
                      <span className="search-result-secondary">
                        {o.customer?.full_name} · {o.status.toUpperCase()} · ₹{parseFloat(o.total_amount).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {!hasResults && (
                <div className="search-no-results">
                  No matches found for "{searchQuery}"
                </div>
              )}
            </div>
          )}
        </div>

        <button className="icon-btn" title="Notifications">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span className="notif-dot" />
        </button>

        <button className="icon-btn" title="Settings">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>
          </svg>
        </button>

        <div className="avatar" title="Admin User">AD</div>
      </div>
    </header>
  );
}
