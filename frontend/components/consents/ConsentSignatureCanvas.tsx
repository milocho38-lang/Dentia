"use client";

import { useEffect, useRef, useState } from "react";
import { SIGNATURE_LOGICAL_HEIGHT, SIGNATURE_LOGICAL_WIDTH, signatureCanvasDimensions } from "@/lib/signatureCanvasSizing.mjs";

export function ConsentSignatureCanvas({ onChange }: { onChange: (value: string | null) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);
  const [hasStroke, setHasStroke] = useState(false);
  const hasStrokeRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const { pixelRatio, width, height } = signatureCanvasDimensions(window.devicePixelRatio);
    canvas.width = width; canvas.height = height;
    const context = canvas.getContext("2d");
    context?.scale(pixelRatio, pixelRatio);
    if (context) { context.fillStyle = "#ffffff"; context.fillRect(0, 0, SIGNATURE_LOGICAL_WIDTH, SIGNATURE_LOGICAL_HEIGHT); context.strokeStyle = "#0f172a"; context.lineWidth = 2.2; context.lineCap = "round"; context.lineJoin = "round"; }
  }, []);

  function point(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!; const rect = canvas.getBoundingClientRect();
    return { x: (event.clientX - rect.left) * (SIGNATURE_LOGICAL_WIDTH / rect.width), y: (event.clientY - rect.top) * (SIGNATURE_LOGICAL_HEIGHT / rect.height) };
  }
  function start(event: React.PointerEvent<HTMLCanvasElement>) { const context=canvasRef.current?.getContext("2d"); if(!context)return; const p=point(event); context.beginPath();context.moveTo(p.x,p.y);setDrawing(true);canvasRef.current?.setPointerCapture(event.pointerId); }
  function move(event: React.PointerEvent<HTMLCanvasElement>) { if(!drawing)return; const context=canvasRef.current?.getContext("2d");if(!context)return;const p=point(event);context.lineTo(p.x,p.y);context.stroke();hasStrokeRef.current=true;setHasStroke(true); }
  function end() { setDrawing(false); if(hasStrokeRef.current&&canvasRef.current)onChange(canvasRef.current.toDataURL("image/png")); }
  function clear() { const canvas=canvasRef.current;const context=canvas?.getContext("2d");if(!canvas||!context)return;context.save();context.setTransform(1,0,0,1,0,0);context.fillStyle="#fff";context.fillRect(0,0,canvas.width,canvas.height);context.restore();hasStrokeRef.current=false;setHasStroke(false);onChange(null); }
  return <div data-has-signature={hasStroke}><canvas ref={canvasRef} onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} className="h-[220px] w-full touch-none rounded-xl border-2 border-dashed border-slate-300 bg-white" aria-label="Área para dibujar la firma" /><button type="button" onClick={clear} className="mt-2 text-sm font-bold text-slate-600">Limpiar firma</button></div>;
}
