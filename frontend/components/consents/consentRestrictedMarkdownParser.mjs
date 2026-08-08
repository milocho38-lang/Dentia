/** Parse Dentia's deliberately small consent Markdown subset without HTML. */
export function parseRestrictedConsentMarkdown(content) {
  const blocks = [];
  const lines = content.replace(/\r\n?/g, "\n").split("\n");
  let paragraph = [];
  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: "paragraph", text: paragraph.join(" ") });
    paragraph = [];
  };
  for (let index = 0; index < lines.length;) {
    const trimmed = lines[index].trim();
    if (!trimmed) { flushParagraph(); index += 1; continue; }
    if (/^#{1,6}\s*$/.test(trimmed)) { flushParagraph(); index += 1; continue; }
    if (trimmed === "---") { flushParagraph(); blocks.push({ type: "separator" }); index += 1; continue; }
    if (trimmed.startsWith("## ")) { flushParagraph(); blocks.push({ type: "h2", text: trimmed.slice(3) }); index += 1; continue; }
    if (trimmed.startsWith("# ")) { flushParagraph(); blocks.push({ type: "h1", text: trimmed.slice(2) }); index += 1; continue; }
    if (/^[-*]\s+/.test(trimmed)) {
      flushParagraph(); const items = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) items.push(lines[index++].replace(/^\s*[-*]\s+/, ""));
      blocks.push({ type: "unordered", items }); continue;
    }
    if (/^\d+\.\s+/.test(trimmed)) {
      flushParagraph(); const items = [];
      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) items.push(lines[index++].replace(/^\s*\d+\.\s+/, ""));
      blocks.push({ type: "ordered", items }); continue;
    }
    paragraph.push(trimmed); index += 1;
  }
  flushParagraph();
  return blocks;
}
