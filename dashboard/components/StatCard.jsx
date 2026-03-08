export default function StatCard({ label, value, tone = "default" }) {
  const toneStyles = {
    default: "text-text",
    accent: "text-accent",
    warning: "text-warning",
    danger: "text-danger"
  };

  return (
    <article className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <p className="text-sm uppercase tracking-wider text-muted">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${toneStyles[tone] || toneStyles.default}`}>{value}</p>
    </article>
  );
}
