export interface NavigationItem {
  label: string;
  href: string;
  permission: string;
  section: "Operación" | "Configuración";
}

export const navigationItems: NavigationItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    permission: "dashboard.view",
    section: "Operación",
  },
  {
    label: "Agenda",
    href: "/agenda",
    permission: "appointments.view",
    section: "Operación",
  },
  {
    label: "Pacientes",
    href: "/pacientes",
    permission: "patients.view",
    section: "Operación",
  },
  {
    label: "Seguimientos",
    href: "/seguimientos",
    permission: "followups.view",
    section: "Operación",
  },
  {
    label: "Empresas",
    href: "/configuracion/empresas",
    permission: "platform.companies.view",
    section: "Configuración",
  },
  {
    label: "Empresa",
    href: "/configuracion/empresa",
    permission: "company.view",
    section: "Configuración",
  },
  {
    label: "Sedes",
    href: "/configuracion/sedes",
    permission: "sites.view",
    section: "Configuración",
  },
  {
    label: "Odontólogos",
    href: "/configuracion/odontologos",
    permission: "sites.view",
    section: "Configuración",
  },
  {
    label: "Usuarios",
    href: "/configuracion/usuarios",
    permission: "users.view",
    section: "Configuración",
  },
];
