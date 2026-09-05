import Link from "next/link";
import { appUrl } from "@/lib/site";
import { Brand } from "./Brand";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div className="site-footer__brand">
          <Brand inverse />
          <p>Una operación odontológica clara, segura y conectada.</p>
          <span>Colombia / Chile</span>
        </div>
        <div>
          <h2>Conocer Dentia</h2>
          <Link href="/producto">Producto</Link>
          <Link href="/precios">Precios</Link>
          <Link href="/seguridad">Seguridad</Link>
        </div>
        <div>
          <h2>Comenzar</h2>
          <Link href="/demo">Solicitar demo</Link>
          <a href={`${appUrl}/login`}>Iniciar sesión</a>
        </div>
        <div>
          <h2>Información</h2>
          <Link href="/privacidad">Política de privacidad</Link>
          <Link href="/terminos">Términos y condiciones</Link>
        </div>
      </div>
      <div className="container site-footer__bottom">
        <span>© {new Date().getFullYear()} Dentia.</span>
        <span>Gestión odontológica diseñada para la operación real.</span>
      </div>
    </footer>
  );
}
