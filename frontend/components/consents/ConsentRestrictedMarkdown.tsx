import { Fragment, type ReactNode } from "react";
import { parseRestrictedConsentMarkdown } from "@/components/consents/consentRestrictedMarkdownParser.mjs";

function inline(text: string): ReactNode[] {
  const tokens = text.split(/(\*\*[^*\n]+\*\*|\*[^*\n]+\*|_[^_\n]+_)/g);
  return tokens.filter(Boolean).map((token, index) => {
    if (token.startsWith("**") && token.endsWith("**")) return <strong key={index}>{token.slice(2, -2)}</strong>;
    if ((token.startsWith("*") && token.endsWith("*")) || (token.startsWith("_") && token.endsWith("_"))) {
      return <em key={index}>{token.slice(1, -1)}</em>;
    }
    return <Fragment key={index}>{token}</Fragment>;
  });
}

export function ConsentRestrictedMarkdown({ content, className = "" }: { content: string; className?: string }) {
  const blocks = parseRestrictedConsentMarkdown(content);
  return <div className={`space-y-3 text-sm leading-7 text-slate-700 ${className}`.trim()}>{blocks.map((block, index) => {
    if (block.type === "separator") return <hr key={index} className="border-slate-200" />;
    if (block.type === "h1") return <h2 key={index} className="text-xl font-black text-slate-950">{inline(block.text)}</h2>;
    if (block.type === "h2") return <h3 key={index} className="text-lg font-black text-slate-900">{inline(block.text)}</h3>;
    if (block.type === "unordered") return <ul key={index} className="list-disc space-y-1 pl-6">{block.items.map((item, itemIndex) => <li key={itemIndex}>{inline(item)}</li>)}</ul>;
    if (block.type === "ordered") return <ol key={index} className="list-decimal space-y-1 pl-6">{block.items.map((item, itemIndex) => <li key={itemIndex}>{inline(item)}</li>)}</ol>;
    if (block.type === "paragraph") return <p key={index}>{inline(block.text)}</p>;
    return null;
  })}</div>;
}
