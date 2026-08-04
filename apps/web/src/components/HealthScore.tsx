import { formatScoreGrade } from "@/lib/format";

export function HealthScore({ score, grade }: { score: number; grade?: string }) {
  const g = grade || formatScoreGrade(score);
  const tone = score >= 80 ? "ok" : score >= 60 ? "warn" : "crit";
  return (
    <div className="panel" style={{ padding: "10px 14px", minWidth: 110, textAlign: "center" }}>
      <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Health</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: `var(--${tone})` }}>{score}</div>
      <div className={`badge ${tone}`}>{g}</div>
    </div>
  );
}
