import Link from "next/link";

export default function NotFound() {
  return (
    <section className="section empty-page">
      <div className="container narrow prose-card">
        <p className="eyebrow">Página no encontrada</p>
        <h1>Esta ruta no está disponible.</h1>
        <p>Vuelve al inicio para seguir conociendo Dentia.</p>
        <Link className="button button--primary" href="/">
          Ir al inicio
        </Link>
      </div>
    </section>
  );
}
