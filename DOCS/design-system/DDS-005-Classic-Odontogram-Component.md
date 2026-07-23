DDS-005 — Classic Odontogram Component
Componente de odontograma clínico clásico Dentia
Versión: 1.0
Estado: Diseño aprobado pendiente de implementación
1. Propósito
Definir el componente oficial de odontograma clínico clásico de Dentia.
Este componente será responsable de la representación clínica rápida del estado dental del paciente, utilizando convenciones odontológicas conocidas.
Su objetivo principal es:
lectura inmediata;
ubicación precisa;
interpretación sin ambigüedad;
compatibilidad con la práctica odontológica tradicional.
2. Decisión de diseño
Dentia utilizará dos representaciones complementarias:
Odontograma clásico
Responsable de:
diagnóstico visual rápido;
ubicación de superficies;
hallazgos;
tratamientos;
estados dentales.
Tooth Component 3D
Responsable de:
anatomía visual;
explicación del estado del diente;
Dental Inspector;
evolución clínica;
comparación;
presentación al paciente.
3. Principio fundamental
El odontograma no es una ilustración.
Es un mapa clínico.
La representación debe priorizar:
precisión clínica;
interpretación rápida;
lenguaje odontológico conocido.
La estética visual nunca debe generar dudas.
4. Arquitectura
La estructura será:
Paciente

   ↓

Classic Odontogram Component

   ↓ seleccionar pieza

Dental Inspector

   ↓

Tooth Component 3D
5. Representación dental
El componente clásico utilizará una representación:
esquemática;
plana;
consistente;
sin perspectiva.
No utilizará una representación anatómica 3D como mapa principal.
6. Piezas dentales
Debe soportar:
dentición permanente;
dentición temporal;
dentición mixta si aplica.
Debe utilizar nomenclatura:
FDI.
Ejemplo:
Superior:
18 17 16 15 14 13 12 11
21 22 23 24 25 26 27 28
Inferior:
48 47 46 45 44 43 42 41
31 32 33 34 35 36 37 38
7. Superficies clínicas
Cada pieza debe permitir representar:
oclusal;
mesial;
distal;
vestibular;
palatina;
lingual;
incisal;
cervical cuando aplique.
La ubicación del símbolo debe corresponder a la superficie afectada.
No utilizar símbolos cuya ubicación pueda generar interpretación incorrecta.
8. Símbolos clínicos
Los símbolos deben seguir un lenguaje odontológico reconocible.
Ejemplos iniciales:
Diagnósticos
Caries:
símbolo rojo;
ubicación según superficie.
Fractura:
símbolo específico.
Lesión cervical:
símbolo ubicado en zona cervical.
Movilidad:
símbolo periodontal.
Lesión periapical:
representación relacionada con raíz/ápice.
Furca:
símbolo periodontal específico.
Tratamientos
Restauración:
símbolo azul.
Endodoncia:
representación interna convencional.
Corona:
símbolo protésico.
Implante:
símbolo implantológico.
Extracción:
símbolo de ausencia/extracción.
9. Selección del diente
Cuando el usuario seleccione una pieza:
Debe existir:
resaltado claro;
identificación FDI;
actualización del panel derecho.
La selección no debe modificar la representación clínica.
10. Relación con Dental Inspector
El odontograma responde:
¿Qué tiene esta pieza y dónde está?

Dental Inspector responde:
¿Cuál es la historia completa de esta pieza?

El odontograma no debe contener toda la información clínica.
11. Relación con Tooth Component
El Tooth Component existente no se elimina.
Continúa siendo utilizado para:
vista detallada;
evolución;
tratamientos;
explicación anatómica.
No reemplaza al odontograma clásico.
12. UX esperada
El odontólogo debe poder:
abrir el paciente;
observar rápidamente el odontograma;
identificar piezas con problemas;
seleccionar una pieza;
revisar detalle en Dental Inspector.
El flujo debe requerir mínima interpretación.
13. Restricciones
No implementar:
representación 3D como mapa clínico;
manchas ambiguas sobre anatomía;
símbolos sin ubicación definida;
colores sin significado clínico.
14. Criterios de aceptación
El componente será aprobado cuando:
✅ Un odontólogo pueda interpretar el odontograma sin explicación adicional.
✅ La ubicación de cada hallazgo sea clara.
✅ No exista ambigüedad entre superficies.
✅ El lenguaje sea familiar para profesionales odontológicos.
✅ Se integre correctamente con Dental Inspector.
