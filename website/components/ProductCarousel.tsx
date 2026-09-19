"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FocusEvent,
  type KeyboardEvent,
} from "react";
import {
  AUTOPLAY_DELAY_MS,
  MANUAL_INTERACTION_PAUSE_MS,
  getNextCarouselSlideIndex,
  shouldRunCarouselAutoplay,
} from "@/lib/carouselAutoplay";
import { screenshots } from "@/lib/screenshots";
import { ProductScreenshot } from "./ProductScreenshot";

const slides = [
  {
    key: "agenda",
    title: "Agenda organizada",
    shortTitle: "Agenda",
    benefit: "Cada cita conserva el contexto para atender mejor.",
    description: "Visualiza disponibilidad, estados y la actividad diaria de tu práctica en un solo lugar.",
    image: screenshots.agenda,
    alt: "Agenda mensual de Dentia con citas odontológicas organizadas por estado",
  },
  {
    key: "pacientes",
    title: "Pacientes en contexto",
    shortTitle: "Pacientes",
    benefit: "La información importante acompaña cada interacción.",
    description: "Encuentra rápidamente los datos administrativos y clínicos de cada paciente.",
    image: screenshots.pacientes,
    alt: "Listado de pacientes en Dentia con filtros, estados e información de contacto",
  },
  {
    key: "historia-clinica",
    title: "Historia clínica trazable",
    shortTitle: "Historia",
    benefit: "Evoluciones y antecedentes en una línea de tiempo clara.",
    description: "Registra la atención y consulta el recorrido clínico sin separar el contexto del paciente.",
    image: screenshots.historiaClinica,
    alt: "Historia clínica de Dentia con evolución firmada y línea de tiempo",
  },
  {
    key: "odontograma",
    title: "Odontograma clínico",
    shortTitle: "Odontograma",
    benefit: "Hallazgos y tratamientos visibles por pieza y superficie.",
    description: "Consulta el estado odontológico con una representación clínica conectada al expediente.",
    image: screenshots.odontograma,
    alt: "Odontograma clínico dual de Dentia con Dental Inspector",
  },
  {
    key: "tratamientos",
    title: "Tratamientos conectados",
    shortTitle: "Tratamientos",
    benefit: "Lo planeado, realizado y pendiente permanece visible.",
    description: "Organiza procedimientos, responsables, estados y presupuestos con continuidad clínica.",
    image: screenshots.tratamientos,
    alt: "Tratamientos odontológicos en Dentia con estado, responsable y saldo",
  },
  {
    key: "consentimientos",
    title: "Consentimientos gestionados",
    shortTitle: "Consentimientos",
    benefit: "El proceso documental forma parte de la atención.",
    description: "Prepara plantillas y gestiona consentimientos electrónicos o digitalizados desde Dentia.",
    image: screenshots.consentimientos,
    alt: "Configuración y gestión de plantillas de consentimientos en Dentia",
  },
  {
    key: "finanzas",
    title: "Finanzas del paciente",
    shortTitle: "Finanzas",
    benefit: "Pagos y saldos permanecen junto al proceso de atención.",
    description: "Registra movimientos, consulta saldos y conserva comprobantes sin fragmentar la operación.",
    image: screenshots.finanzas,
    alt: "Panel financiero de Dentia con ingresos, saldos y tratamientos activos",
  },
  {
    key: "seguimientos",
    title: "Seguimientos visibles",
    shortTitle: "Seguimiento",
    benefit: "Los próximos controles no se pierden de vista.",
    description: "Identifica pacientes pendientes, próximos, vencidos o ya programados.",
    image: screenshots.seguimientos,
    alt: "Seguimientos de pacientes en Dentia clasificados por prioridad y estado",
  },
] as const;

export function ProductCarousel() {
  const regionRef = useRef<HTMLElement>(null);
  const trackRef = useRef<HTMLOListElement>(null);
  const slideRefs = useRef<Array<HTMLLIElement | null>>([]);
  const scrollFrameRef = useRef<number | null>(null);
  const interactionResumeTimeoutRef = useRef<number | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [userPaused, setUserPaused] = useState(false);
  const [interactionPaused, setInteractionPaused] = useState(false);
  const [hoverPaused, setHoverPaused] = useState(false);
  const [focusPaused, setFocusPaused] = useState(false);
  const [pageVisible, setPageVisible] = useState(true);
  const [inViewport, setInViewport] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [announcement, setAnnouncement] = useState("");

  const pauseForManualInteraction = useCallback(() => {
    setInteractionPaused(true);
    if (interactionResumeTimeoutRef.current !== null) {
      window.clearTimeout(interactionResumeTimeoutRef.current);
    }
    interactionResumeTimeoutRef.current = window.setTimeout(() => {
      interactionResumeTimeoutRef.current = null;
      setInteractionPaused(false);
    }, MANUAL_INTERACTION_PAUSE_MS);
  }, []);

  const scrollToSlide = useCallback(
    (index: number, manual = false) => {
      const normalizedIndex = (index + slides.length) % slides.length;
      const track = trackRef.current;
      const slide = slideRefs.current[normalizedIndex];

      if (!track || !slide) {
        return;
      }

      if (manual) {
        pauseForManualInteraction();
        setAnnouncement(`${slides[normalizedIndex].title}, ${normalizedIndex + 1} de ${slides.length}`);
      }

      setActiveIndex(normalizedIndex);
      track.scrollTo({ left: slide.offsetLeft, behavior: reducedMotion ? "auto" : "smooth" });
    },
    [pauseForManualInteraction, reducedMotion],
  );

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotionPreference = () => setReducedMotion(media.matches);
    updateMotionPreference();
    media.addEventListener("change", updateMotionPreference);
    return () => media.removeEventListener("change", updateMotionPreference);
  }, []);

  useEffect(() => {
    const region = regionRef.current;
    if (!region) return;

    const observer = new IntersectionObserver(
      ([entry]) => setInViewport(entry.isIntersecting && entry.intersectionRatio >= 0.15),
      { threshold: [0, 0.15, 1] },
    );
    observer.observe(region);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const updateVisibility = () => setPageVisible(document.visibilityState === "visible");
    updateVisibility();
    document.addEventListener("visibilitychange", updateVisibility);
    return () => document.removeEventListener("visibilitychange", updateVisibility);
  }, []);

  useEffect(() => {
    if (!shouldRunCarouselAutoplay({
      reducedMotion,
      userPaused,
      interactionPaused,
      hoverPaused,
      focusPaused,
      pageVisible,
      inViewport,
    })) return;
    const timeout = window.setTimeout(
      () => scrollToSlide(getNextCarouselSlideIndex(activeIndex, slides.length)),
      AUTOPLAY_DELAY_MS,
    );
    return () => window.clearTimeout(timeout);
  }, [activeIndex, focusPaused, hoverPaused, inViewport, interactionPaused, pageVisible, reducedMotion, scrollToSlide, userPaused]);

  useEffect(
    () => () => {
      if (scrollFrameRef.current !== null) window.cancelAnimationFrame(scrollFrameRef.current);
      if (interactionResumeTimeoutRef.current !== null) {
        window.clearTimeout(interactionResumeTimeoutRef.current);
      }
    },
    [],
  );

  const handleScroll = () => {
    if (scrollFrameRef.current !== null) window.cancelAnimationFrame(scrollFrameRef.current);
    scrollFrameRef.current = window.requestAnimationFrame(() => {
      const track = trackRef.current;
      if (!track) return;

      let closestIndex = activeIndex;
      let closestDistance = Number.POSITIVE_INFINITY;
      slideRefs.current.forEach((slide, index) => {
        if (!slide) return;
        const distance = Math.abs(slide.offsetLeft - track.scrollLeft);
        if (distance < closestDistance) {
          closestDistance = distance;
          closestIndex = index;
        }
      });

      if (closestIndex !== activeIndex) {
        setActiveIndex(closestIndex);
        if (interactionPaused) {
          setAnnouncement(`${slides[closestIndex].title}, ${closestIndex + 1} de ${slides.length}`);
        }
      }
    });
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      scrollToSlide(activeIndex - 1, true);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      scrollToSlide(activeIndex + 1, true);
    }
  };

  const handleBlur = (event: FocusEvent<HTMLElement>) => {
    if (!event.currentTarget.contains(event.relatedTarget)) setFocusPaused(false);
  };

  const handleFocus = (event: FocusEvent<HTMLElement>) => {
    const target = event.target;
    setFocusPaused(target instanceof HTMLElement && target.matches(":focus-visible"));
  };

  return (
    <section
      ref={regionRef}
      className="product-carousel section"
      aria-labelledby="product-carousel-title"
      aria-roledescription="carrusel"
      onBlurCapture={handleBlur}
      onFocusCapture={handleFocus}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setHoverPaused(true)}
      onMouseLeave={() => setHoverPaused(false)}
    >
      <div className="container">
        <div className="section-heading product-carousel__heading">
          <div>
            <p className="eyebrow">Todo conectado en Dentia</p>
            <h2 id="product-carousel-title">El contexto acompaña cada paso de la atención.</h2>
          </div>
          <Link className="text-link" href="/producto">Ver todas las funcionalidades</Link>
        </div>

        <div className="product-carousel__selectors" aria-label="Elegir funcionalidad">
          {slides.map((slide, index) => (
            <button
              type="button"
              key={slide.key}
              className="product-carousel__selector"
              aria-current={activeIndex === index ? "true" : undefined}
              aria-label={`Mostrar ${slide.title}`}
              onClick={() => scrollToSlide(index, true)}
            >
              <span aria-hidden="true" />
              <strong>{slide.shortTitle}</strong>
            </button>
          ))}
        </div>

        <ol
          ref={trackRef}
          className="product-carousel__track"
          aria-label="Funcionalidades principales"
          onPointerDown={pauseForManualInteraction}
          onScroll={handleScroll}
        >
          {slides.map((slide, index) => (
            <li
              ref={(element) => { slideRefs.current[index] = element; }}
              className="product-carousel__slide"
              data-active={activeIndex === index ? "true" : "false"}
              aria-label={`${index + 1} de ${slides.length}: ${slide.title}`}
              key={slide.key}
            >
              <div className="product-carousel__copy">
                <span className="product-carousel__number">{String(index + 1).padStart(2, "0")}</span>
                <h3>{slide.title}</h3>
                <strong>{slide.benefit}</strong>
                <p>{slide.description}</p>
              </div>
              <ProductScreenshot src={slide.image} alt={slide.alt} />
            </li>
          ))}
        </ol>

        <div className="product-carousel__controls" aria-label="Controles del carrusel">
          <button className="carousel-control carousel-control--arrow" type="button" aria-label="Mostrar funcionalidad anterior" onClick={() => scrollToSlide(activeIndex - 1, true)}>
            <span aria-hidden="true">←</span>
          </button>
          <span className="product-carousel__position" aria-hidden="true">{activeIndex + 1} de {slides.length}</span>
          <button
            className="carousel-control carousel-control--pause"
            type="button"
            disabled={reducedMotion}
            aria-pressed={userPaused}
            onClick={() => setUserPaused((paused) => !paused)}
          >
            {reducedMotion ? "Movimiento reducido" : userPaused ? "Reanudar" : "Pausar"}
          </button>
          <button className="carousel-control carousel-control--arrow" type="button" aria-label="Mostrar funcionalidad siguiente" onClick={() => scrollToSlide(activeIndex + 1, true)}>
            <span aria-hidden="true">→</span>
          </button>
        </div>
        <span className="sr-only" aria-live="polite" aria-atomic="true">{announcement}</span>
      </div>
    </section>
  );
}
