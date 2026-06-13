import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOrders } from '../hooks/useOrders';
import { useProducts } from '../hooks/useProducts';
import { useCustomers } from '../hooks/useCustomers';
import StatusBadge from '../components/StatusBadge';
import Drawer from '../components/Drawer';
import { toast } from 'react-toastify';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount);
}

const STATUS_FILTERS = ['All', 'Created', 'Pending', 'Confirmed', 'Cancelled'];

export default function Orders() {
  const navigate = useNavigate();
  const { orders, loading, error, createOrder, deleteOrder } = useOrders();
  const { products } = useProducts();
  const { customers } = useCustomers();

  const [statusFilter, setStatusFilter]  = useState('All');
  const [drawerOpen, setDrawerOpen]      = useState(false);
  const [formError, setFormError]        = useState('');
  const [saving, setSaving]              = useState(false);

  // Order creation form state
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [orderItems, setOrderItems]                  = useState([]);
  const [itemProductId, setItemProductId]            = useState('');
  const [itemQty, setItemQty]                        = useState(1);
  const [itemError, setItemError]                    = useState('');
  const [emailNote, setEmailNote]                    = useState('');

  const filtered = orders.filter((o) =>
    statusFilter === 'All' || o.status === statusFilter.toLowerCase()
  );

  const openCreate = () => {
    setSelectedCustomerId('');
    setOrderItems([]);
    setItemProductId('');
    setItemQty(1);
    setEmailNote('');
    setFormError('');
    setItemError('');
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setEmailNote('');
    setFormError('');
    setItemError('');
  };

  const getProduct = (id) => products.find((p) => p.id === Number(id));

  const addItem = () => {
    setItemError('');
    if (!itemProductId) return setItemError('Select a product.');
    const product = getProduct(itemProductId);
    if (!product) return;
    if (itemQty < 1) return setItemError('Quantity must be at least 1.');
    if (itemQty > product.quantity) {
      return setItemError(`Only ${product.quantity} units in stock.`);
    }

    const existing = orderItems.findIndex((i) => i.product_id === Number(itemProductId));
    if (existing >= 0) {
      // Merge
      const merged = [...orderItems];
      merged[existing] = { ...merged[existing], quantity: merged[existing].quantity + Number(itemQty) };
      setOrderItems(merged);
    } else {
      setOrderItems((prev) => [
        ...prev,
        { product_id: Number(itemProductId), quantity: Number(itemQty), product },
      ]);
    }
    setItemProductId('');
    setItemQty(1);
  };

  const removeItem = (idx) => setOrderItems((prev) => prev.filter((_, i) => i !== idx));

  const orderTotal = orderItems.reduce(
    (sum, item) => sum + parseFloat(item.product.price) * item.quantity,
    0
  );

  const handleCreateOrder = async () => {
    setFormError('');
    if (!selectedCustomerId) return setFormError('Select a customer.');
    if (orderItems.length === 0) return setFormError('Add at least one item.');

    setSaving(true);
    try {
      await createOrder({
        customer_id: Number(selectedCustomerId),
        items: orderItems.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        email_note: emailNote.trim() || null,
      });
      toast.success('Order placed successfully!');
      closeDrawer();
    } catch (err) {
      setFormError(err.message);
      toast.error(`Order creation failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (order) => {
    if (!window.confirm(`Cancel order #${order.id}? Stock will be restored.`)) return;
    try {
      await deleteOrder(order.id);
      toast.success('Order cancelled successfully.');
    } catch (err) {
      toast.error(`Cancellation failed: ${err.message}`);
    }
  };

  return (
    <div className="page-content">
      <div className="page-inner">
        <div className="page-topbar">
          <div className="page-topbar-left">
            <h1 className="page-title">Orders</h1>
            <div className="filter-tabs">
              {STATUS_FILTERS.map((f) => (
                <button
                  key={f}
                  className={`filter-tab${statusFilter === f ? ' active' : ''}`}
                  onClick={() => setStatusFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <button className="btn btn-primary" onClick={openCreate}>
            + Create Order
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order #</th>
                  <th>Customer</th>
                  <th>Products</th>
                  <th style={{ textAlign: 'right' }}>Total</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={7}>Loading…</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={7} className="empty-state">No orders found.</td></tr>
                ) : filtered.map((o) => (
                  <tr key={o.id}>
                    <td className="td-mono">#{String(o.id).padStart(4, '0')}</td>
                    <td style={{ fontWeight: 500 }}>{o.customer?.full_name}</td>
                    <td className="text-secondary">{o.items?.length ?? 0} items</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                      {formatCurrency(o.total_amount)}
                    </td>
                    <td><StatusBadge status={o.status} /></td>
                    <td className="text-meta" style={{ fontSize: '12px' }}>
                      {new Date(o.created_at).toLocaleDateString('en-IN')}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '14px' }}>
                        <button
                          className="action-link action-link-view"
                          onClick={() => navigate(`/orders/${o.id}`)}
                        >
                          View
                        </button>
                        {(o.status === 'created' || o.status === 'pending') && (
                          <button className="action-link action-link-delete" onClick={() => handleCancel(o)}>
                            Cancel
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create Order Drawer */}
      <Drawer
        open={drawerOpen}
        onClose={closeDrawer}
        title="Create Order"
        size="md"
        footer={
          <>
            <button className="btn-ghost" onClick={closeDrawer}>Cancel</button>
            <button className="btn btn-primary" onClick={handleCreateOrder} disabled={saving}>
              {saving ? 'Placing…' : 'Place Order'}
            </button>
          </>
        }
      >
        {formError && <div className="alert alert-error">{formError}</div>}

        {/* Section 1: Customer */}
        <div className="form-group">
          <label className="form-label">Customer</label>
          <select
            className="form-select"
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
          >
            <option value="">— Select a customer —</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Email Note <span className="text-meta">(optional)</span></label>
          <textarea
            className="form-input"
            value={emailNote}
            onChange={(e) => setEmailNote(e.target.value)}
            placeholder="Add an optional note to include in the order confirmation email..."
            style={{ padding: 8, height: 70, resize: 'vertical' }}
          />
        </div>

        {/* Section 2: Add Items */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, marginTop: 8 }}>
          <p className="label-caps" style={{ marginBottom: 12 }}>Order Items</p>

          <div className="add-item-row">
            <div>
              <select
                className="form-select"
                value={itemProductId}
                onChange={(e) => { setItemProductId(e.target.value); setItemError(''); }}
              >
                <option value="">— Select product —</option>
                {products.filter((p) => p.quantity > 0).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} — ₹{parseFloat(p.price).toFixed(2)} ({p.quantity} in stock)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <input
                className="form-input"
                type="number"
                min="1"
                value={itemQty}
                onChange={(e) => { setItemQty(e.target.value); setItemError(''); }}
                placeholder="Qty"
              />
            </div>

            <div>
              <button className="btn btn-secondary btn-sm" onClick={addItem}>Add</button>
            </div>
          </div>

          {itemError && <p className="inline-error">{itemError}</p>}

          {/* Added items mini table */}
          {orderItems.length > 0 && (
            <div className="order-items-mini">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th style={{ textAlign: 'right' }}>Price</th>
                    <th style={{ textAlign: 'right' }}>Qty</th>
                    <th style={{ textAlign: 'right' }}>Subtotal</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {orderItems.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 500 }}>{item.product.name}</td>
                      <td className="td-mono" style={{ textAlign: 'right' }}>₹{parseFloat(item.product.price).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }}>{item.quantity}</td>
                      <td className="td-mono" style={{ textAlign: 'right' }}>
                        ₹{(parseFloat(item.product.price) * item.quantity).toFixed(2)}
                      </td>
                      <td>
                        <button
                          style={{ color: 'var(--error)', cursor: 'pointer', background: 'none', border: 'none', fontSize: '12px' }}
                          onClick={() => removeItem(idx)}
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {orderItems.length > 0 && (
            <div className="order-running-total">
              <span className="label">Order Total</span>
              <span className="amount">{formatCurrency(orderTotal)}</span>
            </div>
          )}
        </div>
      </Drawer>
    </div>
  );
}
