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
    label: "Usuarios",
    href: "/configuracion/usuarios",
    permission: "users.view",
  },
];
