import { useState } from 'react';
import { useProducts } from '../hooks/useProducts';
import Drawer from '../components/Drawer';

function QtyCell({ qty }) {
  const cls = qty < 5 ? 'qty-critical' : qty < 10 ? 'qty-warning' : 'qty-ok';
  return <span className={cls}>{qty}</span>;
}

const EMPTY_FORM = { name: '', sku: '', price: '', quantity: 0 };

export default function Products() {
  const { products, loading, error, createProduct, updateProduct, deleteProduct } = useProducts();

  const [search, setSearch]       = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing]     = useState(null); // null = create mode
  const [form, setForm]           = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [saving, setSaving]       = useState(false);

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError('');
    setDrawerOpen(true);
  };

  const openEdit = (product) => {
    setEditing(product);
    setForm({
      name: product.name,
      sku: product.sku,
      price: product.price,
      quantity: product.quantity,
    });
    setFormError('');
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setEditing(null);
    setFormError('');
  };

  const handleField = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSave = async () => {
    setFormError('');
    if (!form.name.trim()) return setFormError('Product name is required.');
    if (!form.sku.trim()) return setFormError('SKU is required.');
    if (form.price === '' || Number(form.price) < 0) return setFormError('Enter a valid price.');

    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        sku: form.sku.trim().toUpperCase(),
        price: parseFloat(form.price),
        quantity: parseInt(form.quantity, 10) || 0,
      };
      if (editing) {
        await updateProduct(editing.id, { name: payload.name, price: payload.price, quantity: payload.quantity });
      } else {
        await createProduct(payload);
      }
      closeDrawer();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Delete "${product.name}"? This cannot be undone.`)) return;
    try {
      await deleteProduct(product.id);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="page-content">
      <div className="page-inner">
        <div className="page-topbar">
          <div className="page-topbar-left">
            <h1 className="page-title">Products</h1>
            <span className="page-topbar-count">({products.length} items)</span>
          </div>
          <div className="page-topbar-right">
            <div className="search-input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                type="text"
                placeholder="Search products…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button className="btn btn-primary" onClick={openCreate}>
              + Add Product
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Product Name</th>
                  <th>SKU</th>
                  <th style={{ textAlign: 'right' }}>Price</th>
                  <th style={{ textAlign: 'right' }}>In Stock</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={6}>Loading…</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={6} className="empty-state">No products found.</td></tr>
                ) : filtered.map((p, i) => (
                  <tr key={p.id}>
                    <td className="text-meta" style={{ fontSize: '12px' }}>{i + 1}</td>
                    <td 
                      style={{ fontWeight: 500 }}
                      title={`Created: ${new Date(p.created_at).toLocaleString('en-IN')}\nUpdated: ${new Date(p.updated_at).toLocaleString('en-IN')}`}
                    >
                      {p.name}
                    </td>
                    <td className="td-mono">{p.sku}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                      ₹{parseFloat(p.price).toFixed(2)}
                    </td>
                    <td style={{ textAlign: 'right' }}><QtyCell qty={p.quantity} /></td>
                    <td>
                      <div style={{ display: 'flex', gap: '14px' }}>
                        <button className="action-link action-link-edit" onClick={() => openEdit(p)}>Edit</button>
                        <button className="action-link action-link-delete" onClick={() => handleDelete(p)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Drawer
        open={drawerOpen}
        onClose={closeDrawer}
        title={editing ? 'Edit Product' : 'Add Product'}
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={closeDrawer}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : editing ? 'Save Changes' : 'Add Product'}
            </button>
          </>
        }
      >
        {formError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{formError}</div>}

        <div className="form-group">
          <label className="form-label">Product Name</label>
          <input className="form-input" name="name" value={form.name} onChange={handleField} placeholder="e.g. Industrial Sealant A" />
        </div>

        <div className="form-group">
          <label className="form-label">SKU / Code</label>
          <input
            className="form-input"
            name="sku"
            value={form.sku}
            onChange={handleField}
            placeholder="e.g. SEA-1004"
            disabled={!!editing}
            style={editing ? { opacity: 0.6 } : {}}
          />
          {!editing && <span className="form-hint">Must be unique. Auto-uppercased.</span>}
          {editing && <span className="form-hint">SKU cannot be changed after creation.</span>}
        </div>

        <div className="form-group">
          <label className="form-label">Price (₹)</label>
          <input className="form-input" name="price" type="number" min="0" step="0.01" value={form.price} onChange={handleField} placeholder="0.00" />
        </div>

        <div className="form-group">
          <label className="form-label">Quantity in Stock</label>
          <input className="form-input" name="quantity" type="number" min="0" value={form.quantity} onChange={handleField} />
        </div>
      </Drawer>
    </div>
  );
}
