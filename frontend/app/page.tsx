const readinessItems = [
  "Consultorio organizado",
  "Atencion clinica clara",
  "Operacion diaria simple",
  "Crecimiento ordenado",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-dentia-background text-dentia-text">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between border-b border-slate-200 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-dentia-primary text-base font-bold text-white shadow-soft">
              D
            </div>
            <div>
              <p className="text-lg font-semibold leading-tight">Dentia</p>
              <p className="text-sm text-slate-500">Gestion odontologica</p>
            </div>
          </div>
          <div className="rounded-full border border-dentia-soft bg-white px-4 py-2 text-sm font-medium text-dentia-primary">
            Clinica moderna
          </div>
        </header>

        <div className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-semibold leading-tight text-dentia-text sm:text-5xl">
              Una base clara para operar consultorios odontologicos.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
              Dentia inicia con una experiencia limpia, profesional y enfocada
              en el trabajo diario del equipo clinico y administrativo.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {readinessItems.map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-dentia-soft bg-white px-4 py-2 text-sm font-medium text-dentia-text shadow-sm"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>

          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Consultorio al dia</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Vista inicial de Dentia
                </p>
              </div>
              <span className="rounded-full bg-dentia-soft px-3 py-1 text-sm font-semibold text-dentia-primary">
                Activo
              </span>
            </div>

            <div className="space-y-4">
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Agenda</p>
                <p className="mt-1 font-semibold">Preparada para organizar el dia</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Pacientes</p>
                <p className="mt-1 font-semibold">Informacion centralizada</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Caja</p>
                <p className="mt-1 font-semibold">Control financiero visible</p>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
