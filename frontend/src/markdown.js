/**
 * Tiny Markdown renderer — returns Lit template parts, never raw HTML.
 * Supports paragraphs, **bold**, `code`, [link](url), lists and line breaks.
 * No `unsafeHTML` anywhere: everything becomes real nodes, so there is no
 * injection surface (and no need for a sanitizer dependency).
 */
import { html, nothing } from 'lit';

const PARAGRAPHS = /\n\s*\n/;
const LINES = /\n/g;

const BOLD = /\*\*([^*]+)\*\*/g;
const CODE = /`([^`]+)`/g;
const LINK = /\[([^\]]+)\]\(([^)\s]+)\)/g;

/** Split inline text into template parts (bold, code, links, plain text). */
function inline(text) {
  const parts = [];
  const regs = [CODE, LINK, BOLD];
  let offset = 0;
  while (offset < text.length) {
    let best = null;
    for (const re of regs) {
      re.lastIndex = offset;
      const match = re.exec(text);
      if (match && (best === null || match.index < best.index)) best = match;
    }
    if (!best) {
      parts.push(text.slice(offset));
      break;
    }
    if (best.index > offset) parts.push(text.slice(offset, best.index));
    if (best[0].startsWith('`')) {
      parts.push(html`<code>${best[1]}</code>`);
    } else if (best[0].startsWith('[')) {
      const href = safeUrl(best[2]);
      parts.push(
        href === null
          ? best[1]
          : html`<a href=${href} target="_blank" rel="noopener noreferrer">${best[1]}</a>`,
      );
    } else {
      parts.push(html`<strong>${best[1]}</strong>`);
    }
    offset = best.index + best[0].length;
  }
  return parts;
}

/** Only http(s) links pass; anything exotic (javascript:, data:…) is stripped. */
function safeUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : null;
  } catch {
    return null;
  }
}

/**
 * Render a Markdown string as Lit template results:
 * blank-line-separated blocks become <p>, grouped "- "/"1. " lines become lists.
 */
export function renderMarkdown(source) {
  return String(source)
    .split(PARAGRAPHS)
    .map((block) => {
      const lines = block.split(LINES);
      // leading {"- "|"\d. "} lines on every line → a list block
      const isList = lines.length > 0 &&
        lines.every((line) => /^\s*(?:-\s|\d+\.\s)/.test(line));
      if (isList) {
        const ordered = /^\s*\d+\./.test(lines[0]);
        const items = lines.map((line) =>
          html`<li>${inline(line.replace(/^\s*(?:-\s|\d+\.\s)/, ''))}</li>`,
        );
        return ordered ? html`<ol>${items}</ol>` : html`<ul>${items}</ul>`;
      }
      // Soft-wrap: single newlines inside a block become <br>
      const content = [];
      lines.forEach((line, index) => {
        if (index > 0) content.push(html`<br />`);
        if (line) content.push(...(inline(line) || [nothing]));
      });
      return html`<p>${content}</p>`;
    });
}
