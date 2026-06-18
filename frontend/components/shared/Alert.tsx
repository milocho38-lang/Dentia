interface AlertProps {
  children: React.ReactNode;
  tone?: "error" | "info" | "warning";
}

const toneClasses = {
  error: "border-red-200 bg-red-50 text-red-800",
  info: "border-sky-200 bg-sky-50 text-sky-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
};

export function Alert({ children, tone = "info" }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-xl border px-4 py-3 text-sm leading-6 ${toneClasses[tone]}`}
    >
      {children}
    </div>
  );
}
