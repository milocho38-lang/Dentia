export interface NavigationItem {
  label: string;
  href: string;
  permission: string;
}

export const navigationItems: NavigationItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    permission: "dashboard.view",
  },
  {
    label: "Agenda",
    href: "/agenda",
    permission: "appointments.view",
  },
  {
    label: "Usuarios",
    href: "/configuracion/usuarios",
    permission: "users.view",
  },
];
