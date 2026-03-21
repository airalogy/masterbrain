/**
 * Parse .aimd content into HTML for preview rendering.
 * Handles:
 *   - {{step|name}} → numbered step headers
 *   - {{var|name: type = default, ...}} → colored inline badges
 *   - ```assigner ... ``` → code block
 *   - Standard markdown headings, bold, italic
 */
export function parseAimd(content: string): string {
  let stepCount = 0;

  // Protect assigner code blocks first
  const assignerBlocks: string[] = [];
  let html = content.replace(/```assigner\n([\s\S]*?)```/g, (_match, code: string) => {
    const idx = assignerBlocks.length;
    assignerBlocks.push(code);
    return `__ASSIGNER_BLOCK_${idx}__`;
  });

  // Protect regular code blocks
  const codeBlocks: string[] = [];
  html = html.replace(/```[\w]*\n?([\s\S]*?)```/g, (_match, code: string) => {
    const idx = codeBlocks.length;
    codeBlocks.push(escapeHtml(code));
    return `__CODE_BLOCK_${idx}__`;
  });

  // {{step|name}} → numbered step heading
  html = html.replace(/\{\{step\|([^}]+)\}\}/g, (_match, name: string) => {
    stepCount++;
    return `<span class="aimd-step">Step ${stepCount} ${escapeHtml(name.trim())}</span>`;
  });

  // {{var|name: type = default, props...}} → inline badge
  html = html.replace(/\{\{var\|([^}]+)\}\}/g, (_match, inner: string) => {
    const parts = inner.split(',');
    const firstPart = parts[0].trim();
    const colonIdx = firstPart.indexOf(':');
    const varName = colonIdx >= 0 ? firstPart.slice(0, colonIdx).trim() : firstPart;
    const typeAndDefault = colonIdx >= 0 ? firstPart.slice(colonIdx + 1).trim() : '';
    const eqIdx = typeAndDefault.indexOf('=');
    const varType = eqIdx >= 0 ? typeAndDefault.slice(0, eqIdx).trim() : typeAndDefault.trim();
    const varDefault = eqIdx >= 0 ? typeAndDefault.slice(eqIdx + 1).trim() : '';
    let label = varName;
    if (varType) label += `: ${varType}`;
    if (varDefault) label += ` = ${varDefault}`;
    return `<span class="aimd-var" title="${escapeHtml(inner)}">${escapeHtml(label)}</span>`;
  });

  // Markdown headings
  html = html.replace(/^#{1,6}\s+(.+)$/gm, (match, text: string) => {
    const level = match.match(/^(#+)/)?.[1].length ?? 1;
    const sizes = ['2xl', 'xl', 'lg', 'base', 'sm', 'xs'];
    const size = sizes[Math.min(level - 1, 5)];
    return `<h${level} class="aimd-h aimd-h${level} text-${size}">${escapeHtml(text)}</h${level}>`;
  });

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Newlines → paragraphs (simple: double newline = new block)
  html = html
    .split(/\n{2,}/)
    .map(para => {
      const trimmed = para.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<span class="aimd-step')) return trimmed;
      if (trimmed.startsWith('__ASSIGNER_BLOCK') || trimmed.startsWith('__CODE_BLOCK')) return trimmed;
      return `<p class="aimd-para">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('\n');

  // Restore code blocks
  html = html.replace(/__CODE_BLOCK_(\d+)__/g, (_match, idx: string) => {
    return `<pre class="aimd-code"><code>${codeBlocks[+idx]}</code></pre>`;
  });

  // Restore assigner blocks
  html = html.replace(/__ASSIGNER_BLOCK_(\d+)__/g, (_match, idx: string) => {
    return `<pre class="aimd-assigner"><code>${escapeHtml(assignerBlocks[+idx])}</code></pre>`;
  });

  return html;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
