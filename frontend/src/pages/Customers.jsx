import { useState } from 'react';
import { useCustomers } from '../hooks/useCustomers';
import Drawer from '../components/Drawer';

function relativeDate(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const days  = Math.floor(diff / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 30)  return `${days} days ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;
  return `${Math.floor(months / 12)} year${Math.floor(months / 12) > 1 ? 's' : ''} ago`;
}

const EMPTY_FORM = { full_name: '', email: '', phone: '' };

export default function Customers() {
  const { customers, loading, error, createCustomer, deleteCustomer } = useCustomers();

  const [search, setSearch]         = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form, setForm]             = useState(EMPTY_FORM);
  const [formError, setFormError]   = useState('');
  const [saving, setSaving]         = useState(false);

  const filtered = customers.filter((c) =>
    c.full_name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setFormError('');
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setFormError('');
  };

  const handleField = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSave = async () => {
    setFormError('');
    if (!form.full_name.trim()) return setFormError('Full name is required.');
    if (!form.email.trim() || !form.email.includes('@')) return setFormError('A valid email is required.');

    setSaving(true);
    try {
      await createCustomer({
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        phone: form.phone.trim() || null,
      });
      closeDrawer();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (customer) => {
    if (!window.confirm(`Delete customer "${customer.full_name}"? This cannot be undone.`)) return;
    try {
      await deleteCustomer(customer.id);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="page-content">
      <div className="page-inner">
        <div className="page-topbar">
          <div className="page-topbar-left">
            <h1 className="page-title">Customers</h1>
            <span className="page-topbar-count">({customers.length} registered)</span>
          </div>
          <div className="page-topbar-right">
            <div className="search-input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                type="text"
                placeholder="Search customers…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button className="btn btn-primary" onClick={openCreate}>
              + Add Customer
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
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={7}>Loading…</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={7} className="empty-state">No customers found.</td></tr>
                ) : filtered.map((c, i) => (
                  <tr key={c.id}>
                    <td className="text-meta" style={{ fontSize: '12px' }}>{i + 1}</td>
                    <td style={{ fontWeight: 500 }}>{c.full_name}</td>
                    <td className="text-secondary">{c.email}</td>
                    <td className="text-meta">{c.phone || '—'}</td>
                    <td>
                      <span className={c.status === 'inactive' ? 'text-cancelled' : 'text-success'} style={{ fontWeight: 500 }}>
                        {c.status ? c.status.charAt(0).toUpperCase() + c.status.slice(1).toLowerCase() : 'Active'}
                      </span>
                    </td>
                    <td className="text-meta" style={{ fontSize: '12px' }} title={c.created_at ? `Created: ${new Date(c.created_at).toLocaleString('en-IN')}` : ''}>
                      {relativeDate(c.created_at)}
                    </td>
                    <td>
                      <button className="action-link action-link-delete" onClick={() => handleDelete(c)}>Delete</button>
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
        title="Add Customer"
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={closeDrawer}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Add Customer'}
            </button>
          </>
        }
      >
        {formError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{formError}</div>}

        <div className="form-group">
          <label className="form-label">Full Name</label>
          <input className="form-input" name="full_name" value={form.full_name} onChange={handleField} placeholder="e.g. Rahul Sharma" />
        </div>

        <div className="form-group">
          <label className="form-label">Email Address</label>
          <input className="form-input" name="email" type="email" value={form.email} onChange={handleField} placeholder="rahul@example.com" />
          <span className="form-hint">Must be unique across all customers.</span>
        </div>

        <div className="form-group">
          <label className="form-label">Phone <span className="text-meta">(optional)</span></label>
          <input className="form-input" name="phone" type="tel" value={form.phone} onChange={handleField} placeholder="+91 98765 43210" />
        </div>
      </Drawer>
    </div>
  );
}
