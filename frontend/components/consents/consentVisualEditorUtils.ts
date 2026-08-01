import type { ConsentCatalogItem } from "@/types/consentTemplate";

export type VisualBlockType = "paragraph" | "title" | "subtitle" | "bullet" | "number" | "separator";

export type VisualInlineNode =
  | { type: "text"; value: string }
  | { type: "consentVariable"; technicalName: string; displayLabel: string; description: string; known: boolean }
  | { type: "bold"; children: VisualInlineNode[] };

export interface VisualBlock {
  type: VisualBlockType;
  children: VisualInlineNode[];
  listNumber?: number;
}

export interface VisualDocument {
  blocks: VisualBlock[];
}

export interface VisualDocumentValidation {
  valid: boolean;
  technicalVariables: string[];
  unknownVariables: string[];
}

const TECHNICAL_VARIABLE = /^\{\{\s*([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)\s*\}\}/;

function variableNode(technicalName: string, catalog: ConsentCatalogItem[]): VisualInlineNode {
  const item = catalog.find((candidate) => candidate.code === technicalName);
  return {
    type: "consentVariable",
    technicalName,
    displayLabel: item?.label ?? "Dato automático no reconocido",
    description: item?.description ?? technicalName,
    known: Boolean(item),
  };
}

function appendText(nodes: VisualInlineNode[], value: string) {
  if (!value) return;
  const previous = nodes.at(-1);
  if (previous?.type === "text") previous.value += value;
  else nodes.push({ type: "text", value });
}

function parseInline(value: string, catalog: ConsentCatalogItem[]): VisualInlineNode[] {
  const nodes: VisualInlineNode[] = [];
  let cursor = 0;
  while (cursor < value.length) {
    if (value.startsWith("**", cursor)) {
      const close = value.indexOf("**", cursor + 2);
      if (close >= 0) {
        nodes.push({ type: "bold", children: parseInline(value.slice(cursor + 2, close), catalog) });
        cursor = close + 2;
        continue;
      }
    }
    const variable = value.slice(cursor).match(TECHNICAL_VARIABLE);
    if (variable) {
      nodes.push(variableNode(variable[1], catalog));
      cursor += variable[0].length;
      continue;
    }
    const nextBold = value.indexOf("**", cursor);
    const nextVariable = value.indexOf("{{", cursor);
    const candidates = [nextBold, nextVariable].filter((index) => index >= 0);
    const next = candidates.length ? Math.min(...candidates) : value.length;
    if (next === cursor) {
      appendText(nodes, value[cursor]);
      cursor += 1;
    } else {
      appendText(nodes, value.slice(cursor, next));
      cursor = next;
    }
  }
  return nodes;
}

export function restrictedMarkdownToVisualDocument(content: string, catalog: ConsentCatalogItem[]): VisualDocument {
  const blocks = content.replace(/\r\n?/g, "\n").split("\n").map((line): VisualBlock => {
    if (line === "---") return { type: "separator", children: [] };
    if (line.startsWith("# ")) return { type: "title", children: parseInline(line.slice(2), catalog) };
    if (line.startsWith("## ")) return { type: "subtitle", children: parseInline(line.slice(3), catalog) };
    if (line.startsWith("- ")) return { type: "bullet", children: parseInline(line.slice(2), catalog) };
    if (/^\d+\.\s/.test(line)) return { type: "number", listNumber: Number(line.match(/^\d+/)?.[0] ?? "1"), children: parseInline(line.replace(/^\d+\.\s/, ""), catalog) };
    return { type: "paragraph", children: parseInline(line, catalog) };
  });
  return { blocks: blocks.length ? blocks : [{ type: "paragraph", children: [] }] };
}

function inlineToMarkdown(nodes: VisualInlineNode[]): string {
  return nodes.map((node) => {
    if (node.type === "text") return node.value;
    if (node.type === "consentVariable") return `{{ ${node.technicalName} }}`;
    return `**${inlineToMarkdown(node.children)}**`;
  }).join("");
}

export function visualDocumentToRestrictedMarkdown(document: VisualDocument): string {
  return document.blocks.map((block) => {
    if (block.type === "separator") return "---";
    const content = inlineToMarkdown(block.children);
    if (block.type === "title") return `# ${content}`;
    if (block.type === "subtitle") return `## ${content}`;
    if (block.type === "bullet") return `- ${content}`;
    if (block.type === "number") return `${block.listNumber ?? 1}. ${content}`;
    return content;
  }).join("\n");
}

function visitVariables(nodes: VisualInlineNode[], destination: string[]) {
  for (const node of nodes) {
    if (node.type === "consentVariable") destination.push(node.technicalName);
    else if (node.type === "bold") visitVariables(node.children, destination);
  }
}

export function extractTechnicalVariables(document: VisualDocument): string[] {
  const variables: string[] = [];
  for (const block of document.blocks) visitVariables(block.children, variables);
  return [...new Set(variables)].sort();
}

export function validateVisualDocument(document: VisualDocument, catalog: ConsentCatalogItem[]): VisualDocumentValidation {
  const technicalVariables = extractTechnicalVariables(document);
  const known = new Set(catalog.map((item) => item.code));
  const unknownVariables = technicalVariables.filter((code) => !known.has(code));
  return { valid: unknownVariables.length === 0, technicalVariables, unknownVariables };
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderInline(nodes: VisualInlineNode[]): string {
  return nodes.map((node) => {
    if (node.type === "text") return escapeHtml(node.value);
    if (node.type === "bold") return `<strong>${renderInline(node.children)}</strong>`;
    const colors = node.known ? "bg-emerald-50 text-emerald-800 border-emerald-200" : "bg-red-50 text-red-800 border-red-300";
    return `<span contenteditable="false" tabindex="0" role="button" aria-label="Dato automático: ${escapeHtml(node.displayLabel)}" data-consent-variable="${escapeHtml(node.technicalName)}" title="${escapeHtml(node.description)}" class="mx-0.5 inline-flex rounded-md border px-1.5 py-0.5 text-xs font-bold ${colors}">[${escapeHtml(node.displayLabel)}]</span>`;
  }).join("");
}

export function visualDocumentToHtml(document: VisualDocument): string {
  return document.blocks.map((block) => {
    if (block.type === "separator") return '<div data-block="separator" contenteditable="false"><hr class="my-2 border-slate-300" /></div>';
    const listNumber = block.type === "number" ? ` data-list-number="${block.listNumber ?? 1}" data-list-label="${block.listNumber ?? 1}."` : "";
    return `<div data-block="${block.type}"${listNumber}>${block.children.length ? renderInline(block.children) : "<br>"}</div>`;
  }).join("");
}

function domInlineNodes(nodes: NodeListOf<ChildNode>, catalog: ConsentCatalogItem[]): VisualInlineNode[] {
  const result: VisualInlineNode[] = [];
  for (const node of Array.from(nodes)) {
    if (node.nodeType === Node.TEXT_NODE) {
      appendText(result, node.textContent ?? "");
      continue;
    }
    if (!(node instanceof HTMLElement) || node.tagName === "BR") continue;
    const technicalName = node.dataset.consentVariable;
    if (technicalName) result.push(variableNode(technicalName, catalog));
    else if (node.tagName === "STRONG" || node.tagName === "B") result.push({ type: "bold", children: domInlineNodes(node.childNodes, catalog) });
    else result.push(...domInlineNodes(node.childNodes, catalog));
  }
  return result;
}

export function visualDomToDocument(root: HTMLElement, catalog: ConsentCatalogItem[]): VisualDocument {
  const blocks: VisualBlock[] = [];
  for (const node of Array.from(root.childNodes)) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.textContent) blocks.push({ type: "paragraph", children: [{ type: "text", value: node.textContent }] });
      continue;
    }
    if (!(node instanceof HTMLElement)) continue;
    const type = (node.dataset.block ?? "paragraph") as VisualBlockType;
    blocks.push({ type, listNumber: type === "number" ? Number(node.dataset.listNumber ?? "1") : undefined, children: type === "separator" ? [] : domInlineNodes(node.childNodes, catalog) });
  }
  return { blocks: blocks.length ? blocks : [{ type: "paragraph", children: [] }] };
}

export function technicalToVisualHtml(content: string, catalog: ConsentCatalogItem[]): string {
  return visualDocumentToHtml(restrictedMarkdownToVisualDocument(content, catalog));
}

export function visualEditorToTechnical(root: HTMLElement, catalog: ConsentCatalogItem[]): string {
  return visualDocumentToRestrictedMarkdown(visualDomToDocument(root, catalog));
}

export function variableToVisualHtml(code: string, catalog: ConsentCatalogItem[]): string {
  return visualDocumentToHtml({ blocks: [{ type: "paragraph", children: [variableNode(code, catalog)] }] })
    .replace(/^<div data-block="paragraph">/, "").replace(/<\/div>$/, "");
}

export function plainTextToRestrictedMarkdown(value: string): string {
  return value
    .replace(/\r\n?/g, "\n")
    .replace(/<\s*(script|iframe|style|object|embed)\b[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi, "")
    .replace(/<\s*\/?\s*(script|iframe|img|style|object|embed|link|meta)\b[^>]*>/gi, "")
    .replace(/(?:javascript|vbscript|data\s*:\s*text\/html)\s*:/gi, "")
    .replace(/^[ \t]*[•·][ \t]+/gm, "- ")
    .replace(/^[ \t]*(\d+)[.)][ \t]+/gm, "$1. ")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .trim();
}

function pastedInlineToRestrictedMarkdown(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent ?? "";
  if (!(node instanceof HTMLElement)) return "";
  if (["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "IMG", "LINK", "META"].includes(node.tagName)) return "";
  if (node.tagName === "BR") return "\n";
  const content = Array.from(node.childNodes).map(pastedInlineToRestrictedMarkdown).join("");
  if ((node.tagName === "STRONG" || node.tagName === "B") && content) return `**${content}**`;
  return content;
}

function pastedBlockToRestrictedMarkdown(node: HTMLElement): string[] {
  if (node.tagName === "UL" || node.tagName === "OL") {
    let number = Number(node.getAttribute("start") ?? "1");
    return Array.from(node.children).flatMap((child) => {
      if (!(child instanceof HTMLElement) || child.tagName !== "LI") return [];
      const nestedLists = Array.from(child.children).filter((nested) => nested.tagName === "UL" || nested.tagName === "OL");
      const nestedSet = new Set(nestedLists);
      const content = Array.from(child.childNodes)
        .filter((part) => !(part instanceof HTMLElement && nestedSet.has(part)))
        .map(pastedInlineToRestrictedMarkdown)
        .join("")
        .trim();
      const prefix = node.tagName === "OL" ? `${number++}. ` : "- ";
      return [`${prefix}${content}`, ...nestedLists.flatMap((nested) => pastedBlockToRestrictedMarkdown(nested as HTMLElement))];
    });
  }
  if (node.tagName === "HR") return ["---"];
  const content = Array.from(node.childNodes).map(pastedInlineToRestrictedMarkdown).join("").trim();
  if (node.tagName === "H1") return [`# ${content}`];
  if (["H2", "H3", "H4", "H5", "H6"].includes(node.tagName)) return [`## ${content}`];
  return content.split("\n");
}

/** Converts rich clipboard HTML into the supported format without ever rendering external markup. */
export function richTextHtmlToRestrictedMarkdown(html: string, fallbackText: string): string {
  if (!html || typeof DOMParser === "undefined") return plainTextToRestrictedMarkdown(fallbackText);
  const parsed = new DOMParser().parseFromString(html, "text/html");
  parsed.querySelectorAll("script,style,iframe,object,embed,img,link,meta,svg,math").forEach((node) => node.remove());
  const lines = Array.from(parsed.body.children).flatMap((node) => pastedBlockToRestrictedMarkdown(node as HTMLElement));
  return plainTextToRestrictedMarkdown(lines.length ? lines.join("\n") : (parsed.body.textContent ?? fallbackText));
}

export function groupedConsentVariables(catalog: ConsentCatalogItem[]) {
  const groups = new Map<string, ConsentCatalogItem[]>();
  for (const item of catalog) {
    const category = item.category ?? "Otros";
    groups.set(category, [...(groups.get(category) ?? []), item]);
  }
  return Array.from(groups.entries());
}

export function toggleListBlock(document: VisualDocument, blockIndex: number, requested: "bullet" | "number"): VisualDocument {
  return {
    blocks: document.blocks.map((block, index) => index === blockIndex
      ? { ...block, type: block.type === requested ? "paragraph" : requested, listNumber: requested === "number" && block.type !== requested ? 1 : undefined }
      : block),
  };
}

export function exitEmptyListBlock(document: VisualDocument, blockIndex: number): VisualDocument {
  return {
    blocks: document.blocks.map((block, index) => index === blockIndex && (block.type === "bullet" || block.type === "number") && inlineToMarkdown(block.children).trim() === ""
      ? { ...block, type: "paragraph" }
      : block),
  };
}
