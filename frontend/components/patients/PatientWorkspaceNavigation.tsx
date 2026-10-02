"use client";

import {
  patientNavigationGroupForTab,
  targetTabForPatientGroup,
  type PatientNavigationGroup,
  type PatientWorkspaceTab,
} from "@/lib/patientNavigation";

interface PatientWorkspaceNavigationProps {
  activeTab: PatientWorkspaceTab;
  groups: PatientNavigationGroup[];
  onNavigate: (tab: PatientWorkspaceTab) => void;
}

export function PatientWorkspaceNavigation({
  activeTab,
  groups,
  onNavigate,
}: PatientWorkspaceNavigationProps) {
  const activeGroupKey = patientNavigationGroupForTab(activeTab);
  const activeGroup = groups.find((group) => group.key === activeGroupKey);
  const activeLabel = activeGroup?.children.find((item) => item.tab === activeTab)?.label
    ?? activeGroup?.label
    ?? "Contenido del paciente";

  return (
    <nav
      aria-label="Navegación del paciente"
      className="sticky top-0 z-20 mt-6 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-sm backdrop-blur"
      data-patient-navigation="grouped"
    >
      <div
        aria-label="Secciones principales del paciente"
        className="overflow-x-auto overscroll-x-contain [scrollbar-width:thin] lg:overflow-visible"
      >
        <div className="flex min-w-max gap-1.5 lg:min-w-0 lg:flex-wrap">
          {groups.map((group) => {
            const selected = group.key === activeGroupKey;
            const targetTab = targetTabForPatientGroup(group, activeTab);
            return (
              <button
                key={group.key}
                type="button"
                aria-current={selected ? "page" : undefined}
                aria-controls="patient-workspace-panel"
                disabled={!targetTab}
                onClick={() => targetTab && onNavigate(targetTab)}
                className={`min-h-11 rounded-xl px-4 py-2 text-sm font-black transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-600 focus-visible:ring-offset-2 sm:px-5 ${
                  selected
                    ? "bg-dentia-primary text-white shadow-sm"
                    : "text-slate-600 hover:bg-green-50 hover:text-green-800"
                }`}
              >
                {group.label}
              </button>
            );
          })}
        </div>
      </div>

      {activeGroup && activeGroup.children.length > 0 && (
        <div
          aria-label={`Opciones de ${activeGroup.label}`}
          className="mt-1.5 overflow-x-auto overscroll-x-contain border-t border-slate-100 pt-1.5 [scrollbar-width:thin]"
          data-patient-navigation-level="secondary"
        >
          <div className="flex min-w-max gap-1">
            {activeGroup.children.map((item) => {
              const selected = item.tab === activeTab;
              return (
                <button
                  key={item.tab}
                  id={`patient-navigation-${item.tab}`}
                  type="button"
                  aria-current={selected ? "page" : undefined}
                  aria-controls="patient-workspace-panel"
                  onClick={() => onNavigate(item.tab)}
                  className={`min-h-9 rounded-lg px-3 py-1.5 text-sm font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-600 focus-visible:ring-offset-1 ${
                    selected
                      ? "bg-green-50 text-green-800 ring-1 ring-inset ring-green-200"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <span className="sr-only" aria-live="polite">
        Sección activa: {activeLabel}
      </span>
    </nav>
  );
}
