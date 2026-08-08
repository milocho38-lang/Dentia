export type RestrictedConsentMarkdownBlock =
  | { type: "h1" | "h2" | "paragraph"; text: string }
  | { type: "separator" }
  | { type: "unordered" | "ordered"; items: string[] };

export function parseRestrictedConsentMarkdown(content: string): RestrictedConsentMarkdownBlock[];
