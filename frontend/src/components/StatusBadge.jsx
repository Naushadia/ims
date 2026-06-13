/**
 * StatusBadge — plain colored text, NO pill/badge/background.
 * This is a deliberate design decision: status is communicated via color only.
 */
export default function StatusBadge({ status }) {
  const cls = {
    pending: 'status status-pending',
    confirmed: 'status status-confirmed',
    cancelled: 'status status-cancelled',
  }[status?.toLowerCase()] ?? 'status text-secondary';

  const label = status
    ? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
    : '—';

  return <span className={cls}>{label}</span>;
}
