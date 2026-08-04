export type NavigationItem = {
  href: string;
  label: string;
};

export const operationalNavigation: NavigationItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/devices", label: "Dispositivos" },
  { href: "/tasks", label: "Tarefas" },
  { href: "/firmwares", label: "Firmwares" },
];

export function isNavigationActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}
