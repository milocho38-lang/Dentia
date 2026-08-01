"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ConsentCatalogItem } from "@/types/consentTemplate";
import {
  groupedConsentVariables,
  plainTextToRestrictedMarkdown,
  richTextHtmlToRestrictedMarkdown,
  technicalToVisualHtml,
  variableToVisualHtml,
  visualEditorToTechnical,
  type VisualBlockType,
} from "@/components/consents/consentVisualEditorUtils";

interface ConsentVisualEditorProps {
  content: string;
  variables: ConsentCatalogItem[];
  editable: boolean;
  onChange: (content: string) => void;
}

export function ConsentVisualEditor({ content, variables, editable, onChange }: ConsentVisualEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const lastSerialized = useRef(content);
  const lastCatalogSignature = useRef("");
  const savedRange = useRef<Range | null>(null);
  const [advanced, setAdvanced] = useState(false);
  const [showVariables, setShowVariables] = useState(false);
  const [pasteWarning, setPasteWarning] = useState(false);
  const [currentBlockType, setCurrentBlockType] = useState<VisualBlockType>("paragraph");
  const groups = useMemo(() => groupedConsentVariables(variables), [variables]);
  const catalogSignature = useMemo(() => variables.map((item) => `${item.code}:${item.label}`).join("|"), [variables]);

  useEffect(() => {
    if (!advanced && editorRef.current && (editorRef.current.innerHTML === "" || content !== lastSerialized.current || catalogSignature !== lastCatalogSignature.current)) {
      editorRef.current.innerHTML = technicalToVisualHtml(content, variables);
      lastSerialized.current = content;
      lastCatalogSignature.current = catalogSignature;
    }
  }, [advanced, catalogSignature, content, variables]);

  function syncFromVisual() {
    if (!editorRef.current) return;
    const next = visualEditorToTechnical(editorRef.current, variables);
    lastSerialized.current = next;
    onChange(next);
    rememberSelection();
  }

  function rememberSelection() {
    const selection = window.getSelection();
    if (selection?.rangeCount && editorRef.current?.contains(selection.anchorNode)) {
      savedRange.current = selection.getRangeAt(0).cloneRange();
      const element = selection.anchorNode instanceof HTMLElement ? selection.anchorNode : selection.anchorNode?.parentElement;
      const block = element?.closest<HTMLElement>("[data-block]");
      if (block?.dataset.block) setCurrentBlockType(block.dataset.block as VisualBlockType);
    }
  }

  function restoreSelection() {
    const selection = window.getSelection();
    if (!selection || !savedRange.current) return;
    selection.removeAllRanges();
    selection.addRange(savedRange.current);
  }

  function currentBlock() {
    const selection = window.getSelection();
    const anchor = selection?.anchorNode;
    const element = anchor instanceof HTMLElement ? anchor : anchor?.parentElement;
    const block = element?.closest<HTMLElement>("[data-block]") ?? null;
    return block && editorRef.current?.contains(block) ? block : null;
  }

  function toggleBlock(type: VisualBlockType) {
    restoreSelection();
    const block = currentBlock();
    if (!block) return;
    block.dataset.block = block.dataset.block === type && (type === "bullet" || type === "number") ? "paragraph" : type;
    if (block.dataset.block === "number") {
      block.dataset.listNumber = block.dataset.listNumber ?? "1";
      block.dataset.listLabel = `${block.dataset.listNumber}.`;
    } else {
      delete block.dataset.listNumber;
      delete block.dataset.listLabel;
    }
    setCurrentBlockType(block.dataset.block as VisualBlockType);
    syncFromVisual();
  }

  function insertInlineNode(node: Node, trailingSpace = false) {
    editorRef.current?.focus();
    restoreSelection();
    const selection = window.getSelection();
    if (!selection?.rangeCount) return;
    const range = selection.getRangeAt(0);
    range.deleteContents();
    range.insertNode(node);
    const caretNode = trailingSpace ? document.createTextNode(" ") : node;
    if (trailingSpace) node.parentNode?.insertBefore(caretNode, node.nextSibling);
    range.setStartAfter(caretNode);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    syncFromVisual();
  }

  function insertVariable(item: ConsentCatalogItem) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = variableToVisualHtml(item.code, variables);
    const node = wrapper.firstChild;
    if (node) insertInlineNode(node, true);
    setShowVariables(false);
  }

  function insertSeparator() {
    restoreSelection();
    const block = currentBlock();
    if (!block) return;
    const wrapper = document.createElement("div");
    wrapper.innerHTML = technicalToVisualHtml("---\n", variables);
    const separator = wrapper.firstElementChild;
    const paragraph = separator?.nextElementSibling;
    if (separator) block.insertAdjacentElement("afterend", separator);
    if (paragraph) separator?.insertAdjacentElement("afterend", paragraph);
    syncFromVisual();
  }

  function toggleBold() {
    restoreSelection();
    const selection = window.getSelection();
    if (!selection?.rangeCount) return;
    const range = selection.getRangeAt(0);
    const element = range.commonAncestorContainer instanceof HTMLElement ? range.commonAncestorContainer : range.commonAncestorContainer.parentElement;
    const existing = element?.closest("strong");
    if (existing && editorRef.current?.contains(existing)) {
      existing.replaceWith(...Array.from(existing.childNodes));
    } else if (!range.collapsed) {
      const strong = document.createElement("strong");
      strong.appendChild(range.extractContents());
      range.insertNode(strong);
      range.selectNodeContents(strong);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    syncFromVisual();
  }

  function onPaste(event: React.ClipboardEvent<HTMLDivElement>) {
    event.preventDefault();
    const html = event.clipboardData.getData("text/html");
    const text = event.clipboardData.getData("text/plain");
    const clean = html ? richTextHtmlToRestrictedMarkdown(html, text) : plainTextToRestrictedMarkdown(text);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = technicalToVisualHtml(clean, variables);
    const blocks = Array.from(wrapper.children);
    if (blocks.length <= 1) {
      const children = blocks[0] ? Array.from(blocks[0].childNodes) : [];
      for (const child of children) insertInlineNode(child);
    } else {
      restoreSelection();
      const block = currentBlock();
      if (block) {
        for (const pastedBlock of blocks) block.parentNode?.insertBefore(pastedBlock, block);
        if (!(block.textContent ?? "").trim()) block.remove();
        syncFromVisual();
      }
    }
    setPasteWarning(Boolean(html) || clean !== text.replace(/\r\n?/g, "\n").trim());
  }

  function onEditorKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const target = event.target instanceof HTMLElement ? event.target : null;
    if ((event.key === "Backspace" || event.key === "Delete") && target?.dataset.consentVariable) {
      event.preventDefault();
      target.remove();
      syncFromVisual();
      return;
    }
    const block = currentBlock();
    if (!block || !["bullet", "number"].includes(block.dataset.block ?? "")) return;
    const empty = !(block.textContent ?? "").trim();
    if ((event.key === "Enter" || event.key === "Backspace") && empty) {
      event.preventDefault();
      block.dataset.block = "paragraph";
      delete block.dataset.listNumber;
      delete block.dataset.listLabel;
      setCurrentBlockType("paragraph");
      syncFromVisual();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const next = document.createElement("div");
      next.dataset.block = block.dataset.block;
      if (block.dataset.block === "number") {
        next.dataset.listNumber = String(Number(block.dataset.listNumber ?? "1") + 1);
        next.dataset.listLabel = `${next.dataset.listNumber}.`;
      }
      next.appendChild(document.createElement("br"));
      block.insertAdjacentElement("afterend", next);
      const range = document.createRange();
      range.setStart(next, 0);
      range.collapse(true);
      const selection = window.getSelection();
      selection?.removeAllRanges();
      selection?.addRange(range);
      rememberSelection();
      syncFromVisual();
    }
  }

  function toggleAdvanced() {
    if (!advanced) syncFromVisual();
    else lastSerialized.current = content;
    setAdvanced((current) => !current);
    setShowVariables(false);
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-2" role="toolbar" aria-label="Herramientas de edición del consentimiento">
        <button type="button" disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={() => toggleBlock("title")} className="rounded-lg px-2.5 py-2 text-xs font-bold hover:bg-white disabled:opacity-40">Título</button>
        <button type="button" disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={() => toggleBlock("subtitle")} className="rounded-lg px-2.5 py-2 text-xs font-bold hover:bg-white disabled:opacity-40">Subtítulo</button>
        <button type="button" disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={toggleBold} className="rounded-lg px-2.5 py-2 text-xs font-black hover:bg-white disabled:opacity-40">Negrilla</button>
        <button type="button" aria-pressed={currentBlockType === "bullet"} disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={() => toggleBlock("bullet")} className="rounded-lg px-2.5 py-2 text-xs font-bold hover:bg-white disabled:opacity-40">• Lista</button>
        <button type="button" aria-pressed={currentBlockType === "number"} disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={() => toggleBlock("number")} className="rounded-lg px-2.5 py-2 text-xs font-bold hover:bg-white disabled:opacity-40">1. Lista</button>
        {(currentBlockType === "bullet" || currentBlockType === "number") && <button type="button" disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={() => toggleBlock(currentBlockType)} className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs font-bold">Quitar lista</button>}
        <button type="button" disabled={!editable || advanced} onMouseDown={(event) => event.preventDefault()} onClick={insertSeparator} className="rounded-lg px-2.5 py-2 text-xs font-bold hover:bg-white disabled:opacity-40">Separador</button>
        <div className="relative">
          <button type="button" disabled={!editable || advanced} aria-expanded={showVariables} onMouseDown={(event) => event.preventDefault()} onClick={() => setShowVariables((current) => !current)} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-black text-white disabled:opacity-40">Insertar dato automático</button>
          {showVariables && <div className="absolute left-0 top-11 z-30 max-h-96 w-[min(420px,82vw)] overflow-y-auto rounded-xl border border-slate-200 bg-white p-3 shadow-xl" role="menu" aria-label="Datos automáticos disponibles">
            {groups.map(([category, items]) => <section key={category} className="mb-3 last:mb-0"><h4 className="px-2 pb-1 text-[11px] font-black uppercase tracking-wide text-slate-400">{category}</h4><div className="grid gap-1 sm:grid-cols-2">{items.map((item) => <button type="button" role="menuitem" key={item.code} onMouseDown={(event) => event.preventDefault()} onClick={() => insertVariable(item)} className="rounded-lg p-2 text-left hover:bg-emerald-50"><span className="block text-xs font-black text-slate-800">{item.label}</span><span className="mt-0.5 block text-[11px] leading-4 text-slate-500">{item.description}</span></button>)}</div></section>)}
          </div>}
        </div>
        {editable && <button type="button" onClick={toggleAdvanced} className="ml-auto rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-600">{advanced ? "Volver al editor visual" : "Ver código de plantilla"}</button>}
      </div>

      {advanced ? <div><p className="mb-2 text-xs text-amber-700">Modo avanzado: muestra el formato interno y los nombres técnicos. Los cambios se guardan con las mismas reglas de seguridad.</p><textarea value={content} onChange={(event) => { lastSerialized.current = event.target.value; onChange(event.target.value); }} rows={16} maxLength={50000} className="w-full rounded-xl border border-slate-300 p-3 font-mono text-sm leading-6" /></div> : <div
        ref={editorRef}
        contentEditable={editable}
        suppressContentEditableWarning
        onInput={syncFromVisual}
        onKeyDown={onEditorKeyDown}
        onKeyUp={rememberSelection}
        onMouseUp={rememberSelection}
        onFocus={rememberSelection}
        onPaste={onPaste}
        role="textbox"
        aria-multiline="true"
        aria-label="Contenido del consentimiento"
        className="consent-visual-editor min-h-[320px] rounded-xl border border-slate-300 bg-white p-4 text-sm leading-7 text-slate-700 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 [&_[data-block=title]]:text-xl [&_[data-block=title]]:font-black [&_[data-block=subtitle]]:text-lg [&_[data-block=subtitle]]:font-black [&_[data-block=bullet]]:before:mr-2 [&_[data-block=bullet]]:before:content-['•'] [&_[data-block=number]]:before:mr-2 [&_[data-block=number]]:before:content-[attr(data-list-label)]"
      />}
      <div className="flex flex-wrap items-start justify-between gap-2 text-xs text-slate-500"><div><p>Escriba o pegue el texto del consentimiento.</p><p>Use Insertar dato automático para incluir información del paciente, profesional o clínica.</p><p>Dentia completará estos datos cuando se genere el consentimiento para un paciente.</p></div><span>{content.length}/50000</span></div>
      {pasteWarning && <div role="status" className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">Se eliminó formato externo incompatible. Se conservaron el texto, los párrafos y las listas básicas disponibles.</div>}
    </div>
  );
}
