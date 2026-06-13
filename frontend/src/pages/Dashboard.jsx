import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../hooks/useOrders';
import StatusBadge from '../components/StatusBadge';
import { useOrders } from '../hooks/useOrders';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount);
}

function QtyCell({ qty }) {
  const cls = qty < 5 ? 'qty-critical' : qty < 10 ? 'qty-warning' : 'qty-ok';
  return <span className={cls}>{qty}</span>;
}

export default function Dashboard() {
  const { summary, loading } = useDashboard();
  const { orders } = useOrders();
  const navigate = useNavigate();

  const recentOrders = orders.slice(0, 6);

  if (loading || !summary) {
    return (
      <div className="page-content">
        <div className="page-inner">
          <div className="empty-state">Loading dashboard…</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <div className="page-inner">
        {/* KPI Cards */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <span className="label-caps">Total Products</span>
            <div className="kpi-number">{summary.total_products.toLocaleString('en-IN')}</div>
            <p className="kpi-support">Active SKUs in inventory</p>
          </div>

          <div className="kpi-card">
            <span className="label-caps">Total Customers</span>
            <div className="kpi-number">{summary.total_customers.toLocaleString('en-IN')}</div>
            <p className="kpi-support">Registered accounts</p>
          </div>

          <div className="kpi-card">
            <span className="label-caps">Total Orders</span>
            <div className="kpi-number">{summary.total_orders.toLocaleString('en-IN')}</div>
            <p className="kpi-support">All time orders placed</p>
          </div>

          <div className="kpi-card kpi-card-low-stock">
            <span className="label-caps" style={{ color: 'var(--error)' }}>Low Stock Items</span>
            <div className="kpi-number error">{summary.low_stock_count}</div>
            <p className="kpi-support" style={{ color: 'var(--error)', opacity: 0.8 }}>Items below 10 units</p>
          </div>
        </div>

        {/* 60/40 Split */}
        <div className="dashboard-split">
          {/* Recent Orders */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Recent Orders</span>
              <button className="btn-ghost" onClick={() => navigate('/orders')}>
                View all →
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Customer</th>
                    <th>Items</th>
                    <th style={{ textAlign: 'right' }}>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentOrders.length === 0 ? (
                    <tr><td colSpan={5} className="empty-state">No orders yet.</td></tr>
                  ) : recentOrders.map((order) => (
                    <tr
                      key={order.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/orders/${order.id}`)}
                    >
                      <td className="td-mono">#{String(order.id).padStart(4, '0')}</td>
                      <td>{order.customer?.full_name}</td>
                      <td className="text-secondary">{order.items?.length ?? 0} items</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                        {formatCurrency(order.total_amount)}
                      </td>
                      <td><StatusBadge status={order.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Low Stock Alert */}
          <div className="card">
            <div className="card-header">
              <span className="card-title" style={{ color: 'var(--error)' }}>Low Stock Alert</span>
              <button className="btn-ghost" onClick={() => navigate('/products')}>
                View all →
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>SKU</th>
                    <th style={{ textAlign: 'right' }}>Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.low_stock_products.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="empty-state" style={{ color: 'var(--success)' }}>
                        All products are well-stocked.
                      </td>
                    </tr>
                  ) : summary.low_stock_products.slice(0, 6).map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 500 }}>{p.name}</td>
                      <td className="td-mono">{p.sku}</td>
                      <td style={{ textAlign: 'right' }}><QtyCell qty={p.quantity} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
