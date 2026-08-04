export function formatScoreGrade(score: number): string {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

export function onlineLabel(online: boolean): string {
  return online ? "online" : "offline";
}
