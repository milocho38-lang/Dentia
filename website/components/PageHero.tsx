import type { ReactNode } from "react";

export function PageHero({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="page-hero">
      <div className="container page-hero__inner">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <div className="page-hero__copy">{children}</div>
      </div>
    </section>
  );
}
