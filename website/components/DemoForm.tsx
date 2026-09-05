export function DemoForm() {
  return (
    <form className="demo-form" aria-describedby="demo-form-status">
      <div className="form-grid">
        <div className="form-field">
          <label htmlFor="demo-name">Nombre</label>
          <input id="demo-name" name="name" autoComplete="name" type="text" />
        </div>
        <div className="form-field">
          <label htmlFor="demo-email">Email</label>
          <input id="demo-email" name="email" autoComplete="email" type="email" />
        </div>
        <div className="form-field">
          <label htmlFor="demo-phone">Teléfono / WhatsApp</label>
          <input id="demo-phone" name="phone" autoComplete="tel" type="tel" />
        </div>
        <div className="form-field">
          <label htmlFor="demo-country">País</label>
          <select id="demo-country" name="country" defaultValue="">
            <option value="" disabled>Selecciona un país</option>
            <option value="CO">Colombia</option>
            <option value="CL">Chile</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="demo-practice">Tipo de práctica</label>
          <select id="demo-practice" name="practiceType" defaultValue="">
            <option value="" disabled>Selecciona una opción</option>
            <option value="independent">Odontólogo independiente</option>
            <option value="clinic">Clínica o consultorio</option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="demo-dentists">Número aproximado de odontólogos</label>
          <input id="demo-dentists" name="dentists" inputMode="numeric" min="1" type="number" />
        </div>
        <div className="form-field form-field--full">
          <label htmlFor="demo-message">Mensaje opcional</label>
          <textarea id="demo-message" name="message" />
        </div>
      </div>
      <button className="button button--primary" type="submit" disabled>
        Solicitar demostración
      </button>
      <p className="form-disclosure" id="demo-form-status" role="status">
        El envío estará disponible cuando se habilite el canal seguro de solicitudes. Por ahora, el
        formulario se presenta únicamente para revisión visual y no transmite ni almacena información.
      </p>
    </form>
  );
}
