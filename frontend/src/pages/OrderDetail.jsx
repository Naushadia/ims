import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getOrder, updateOrderStatus } from '../api/orders';
import StatusBadge from '../components/StatusBadge';
import { toast } from 'react-toastify';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount);
}

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  
  // Status transition states
  const [updating, setUpdating] = useState(false);
  const [showCancelInput, setShowCancelInput] = useState(false);
  const [remarks, setRemarks] = useState('');
  const [remarksError, setRemarksError] = useState('');

  const fetchOrder = () => {
    setLoading(true);
    getOrder(id)
      .then(setOrder)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOrder();
  }, [id]);

  const handleStatusUpdate = async (newStatus) => {
    if (!window.confirm(`Update order status to "${newStatus.toUpperCase()}"?`)) return;
    setUpdating(true);
    try {
      const updated = await updateOrderStatus(id, newStatus);
      setOrder(updated);
      toast.success(`Order status updated to ${newStatus.toUpperCase()}`);
    } catch (err) {
      toast.error(`Failed to update status: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  const handleCancelSubmit = async () => {
    if (!remarks.trim()) {
      setRemarksError('Please enter a cancellation reason.');
      return;
    }
    setRemarksError('');
    setUpdating(true);
    try {
      const updated = await updateOrderStatus(id, 'cancelled', remarks.trim());
      setOrder(updated);
      setShowCancelInput(false);
      setRemarks('');
      toast.success('Order cancelled successfully.');
    } catch (err) {
      toast.error(`Cancellation failed: ${err.message}`);
    } finally {
      setUpdating(false);
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

            {/* Display cancellation reason if cancelled */}
            {order.status === 'cancelled' && (
              <div className="alert alert-error" style={{ marginTop: 20 }}>
                <strong>Cancellation Remarks:</strong> {order.cancellation_reason || 'No remarks provided.'}
              </div>
            )}
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

            {/* Transition Controls */}
            {!updating && !showCancelInput && order.status === 'created' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => handleStatusUpdate('confirmed')}>
                  Confirm Order
                </button>
                <button className="btn btn-danger-outline" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setShowCancelInput(true)}>
                  Cancel Order
                </button>
              </div>
            )}

            {!updating && !showCancelInput && order.status === 'confirmed' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => handleStatusUpdate('completed')}>
                  Complete Order (Deliver)
                </button>
                <button className="btn btn-danger-outline" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setShowCancelInput(true)}>
                  Cancel Order
                </button>
              </div>
            )}

            {showCancelInput && (
              <div className="detail-card" style={{ border: '1px solid var(--error)' }}>
                <div className="detail-card-title" style={{ color: 'var(--error)' }}>Cancel Order Remarks</div>
                <div className="form-group" style={{ margin: '8px 0 12px' }}>
                  <textarea 
                    className="form-input" 
                    placeholder="Enter cancellation reason..." 
                    style={{ height: 80, padding: 8, resize: 'vertical' }}
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                  />
                  {remarksError && <div className="form-error">{remarksError}</div>}
                </div>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => { setShowCancelInput(false); setRemarks(''); setRemarksError(''); }}>
                    Abort
                  </button>
                  <button className="btn btn-primary btn-sm" style={{ background: 'var(--error)', borderColor: 'var(--error)' }} onClick={handleCancelSubmit}>
                    Confirm Cancel
                  </button>
                </div>
              </div>
            )}

            {updating && (
              <div className="empty-state" style={{ padding: 12 }}>Updating order...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
