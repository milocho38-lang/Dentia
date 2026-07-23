# ADR-002 — Representación dual y sincronizada del diente

## Estado

Aceptado

---

## Contexto

Durante el diseño del Odontograma Dentia 2.0 se evaluaron diferentes formas de representar el estado clínico de cada pieza.

Inicialmente se utilizó un Tooth Component anatómico moderno con diagnósticos y tratamientos dibujados directamente sobre la pieza.

La validación con un odontólogo reveló que esa representación podía generar ambigüedad entre superficies como:

- oclusal;
- vestibular;
- palatina;
- lingual;
- cervical;
- furca.

Posteriormente se analizaron odontogramas clásicos y el flujo utilizado por el software actual del odontólogo.

Se identificó que una representación dual permite conservar simultáneamente:

- la ubicación anatómica esquemática;
- el mapa inequívoco de superficies.

---

## Decisión

Dentia utilizará una representación dual y sincronizada para cada pieza del odontograma principal:

1. Vista anatómica esquemática.
2. Vista superior o mapa de cinco caras.

Ambas vistas serán generadas desde el mismo evento odontográfico y el mismo estado clínico reconstruido.

El Tooth Component anatómico avanzado será utilizado dentro del Dental Inspector y no como mapa principal de las 32 piezas.

---

## Razones

La decisión busca:

- evitar ambigüedades clínicas;
- mantener familiaridad para odontólogos;
- identificar superficies con precisión;
- conservar una experiencia moderna;
- reutilizar el Tooth Component avanzado donde aporta mayor valor;
- evitar doble registro.

---

## Consecuencias positivas

- Lectura clínica más rápida.
- Superficies inequívocas.
- Sincronización entre vista anatómica y mapa superficial.
- Mejor integración con el Dental Inspector.
- Conservación del trabajo realizado en Tooth Component.
- Menor riesgo de interpretación incorrecta.
- Arquitectura extensible para dentición temporal y mixta.

---

## Consecuencias negativas

- Se deben mantener dos representaciones visuales por pieza.
- Aumenta la complejidad del componente clásico.
- Requiere un mapper clínico preciso.
- Exige pruebas de sincronización.
- Requiere una librería gráfica adicional.

---

## Alternativas descartadas

### Usar únicamente Tooth Component anatómico

Descartado porque la perspectiva puede generar ambigüedad entre superficies.

### Usar únicamente mapa de cinco caras

Descartado porque no representa adecuadamente estados anatómicos, radiculares, protésicos o estructurales.

### Registrar eventos independientes por vista

Descartado porque produciría:

- duplicidad;
- inconsistencias;
- errores de sincronización;
- doble trabajo clínico.

---

## Regla arquitectónica

```text
Evento odontográfico
        ↓
Modelo clínico de la pieza
        ├── Vista anatómica
        └── Vista superior de cinco caras
```

El componente visual no crea información clínica.

Solo representa la fuente de verdad existente.

---

## Resultado esperado

Dentia combina:

- precisión clínica clásica;
- representación anatómica esquemática;
- detalle avanzado mediante Dental Inspector;
- Tooth Component moderno para análisis y explicación.
