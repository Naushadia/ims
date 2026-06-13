import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getOrder } from '../api/orders';
import { deleteOrder } from '../api/orders';
import StatusBadge from '../components/StatusBadge';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount);
}

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    setLoading(true);
    getOrder(id)
      .then(setOrder)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleCancel = async () => {
    if (!window.confirm('Cancel this order? Stock will be restored.')) return;
    try {
      await deleteOrder(id);
      navigate('/orders');
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="page-content"><div className="empty-state">Loading order…</div></div>;
  if (error)   return <div className="page-content"><div className="alert alert-error">{error}</div></div>;
  if (!order)  return null;

  return (
    <div className="page-content">
      <div className="page-inner">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <a onClick={() => navigate('/orders')}>← Orders</a>
          <span>/</span>
          <span>Order #{String(order.id).padStart(4, '0')}</span>
        </div>

        {/* Page header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
          <h1 className="page-title">Order #{String(order.id).padStart(4, '0')}</h1>
          <StatusBadge status={order.status} />
          <span className="text-meta" style={{ fontSize: '13px' }}>
            {new Date(order.created_at).toLocaleDateString('en-IN', {
              day: 'numeric', month: 'long', year: 'numeric'
            })}
          </span>
        </div>

        {/* 65/35 split */}
        <div className="detail-split">
          {/* Left — Order Items */}
          <div>
            <div className="card">
              <div className="card-header">
                <span className="card-title">Order Items</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>SKU</th>
                      <th style={{ textAlign: 'right' }}>Unit Price</th>
                      <th style={{ textAlign: 'right' }}>Qty</th>
                      <th style={{ textAlign: 'right' }}>Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.items.map((item) => (
                      <tr key={item.id}>
                        <td style={{ fontWeight: 500 }}>{item.product?.name}</td>
                        <td className="td-mono">{item.product?.sku}</td>
                        <td className="td-mono" style={{ textAlign: 'right' }}>
                          ₹{parseFloat(item.unit_price).toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'right' }}>{item.quantity}</td>
                        <td className="td-mono" style={{ textAlign: 'right' }}>
                          {formatCurrency(item.subtotal)}
                        </td>
                      </tr>
                    ))}
                    {/* Total row */}
                    <tr className="total-row">
                      <td colSpan={3} />
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>Total</td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="total-amount-display">{formatCurrency(order.total_amount)}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right — Customer + Summary */}
          <div>
            {/* Customer card */}
            <div className="detail-card">
              <div className="detail-card-title">Customer</div>
              <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>
                {order.customer?.full_name}
              </div>
              <div className="detail-row">
                <span className="dlabel">Email</span>
                <span className="dvalue" style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                  {order.customer?.email}
                </span>
              </div>
            </div>

            {/* Summary card */}
            <div className="detail-card">
              <div className="detail-card-title">Order Summary</div>
              <div className="detail-row">
                <span className="dlabel">Status</span>
                <span className="dvalue"><StatusBadge status={order.status} /></span>
              </div>
              <div className="detail-row">
                <span className="dlabel">Order ID</span>
                <span className="dvalue td-mono">#{String(order.id).padStart(4, '0')}</span>
              </div>
              <div className="detail-row">
                <span className="dlabel">Placed</span>
                <span className="dvalue">
                  {new Date(order.created_at).toLocaleDateString('en-IN')}
                </span>
              </div>
              <div className="detail-row">
                <span className="dlabel">Items</span>
                <span className="dvalue">{order.items.length}</span>
              </div>
            </div>

            {/* Cancel button — only for pending */}
            {order.status === 'pending' && (
              <button className="btn btn-danger-outline" style={{ width: '100%' }} onClick={handleCancel}>
                Cancel Order
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
