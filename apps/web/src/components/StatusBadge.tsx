export function StatusBadge({ online }: { online: boolean }) {
  return <span className={`badge ${online ? "ok" : "crit"}`}>{online ? "online" : "offline"}</span>;
}
