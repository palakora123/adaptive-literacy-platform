'use client';

import React from 'react';

/**
 * Minimal Markdown renderer for lesson bodies.
 *
 * The lesson content is authored in this repo, not user-supplied, and covers a
 * known subset: headings, bold/italic/code, tables, blockquotes, ordered and
 * unordered lists. A full Markdown library would be a large dependency for
 * that, so this handles the subset and renders anything else as plain text.
 * Because it never emits raw HTML, unexpected input degrades to text rather
 * than becoming an injection vector.
 */

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // Order matters: ** before *, so bold is not eaten by the italic rule.
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  const parts = text.split(pattern);

  parts.forEach((part, index) => {
    if (!part) return;
    const key = `${keyPrefix}-${index}`;
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      nodes.push(
        <strong key={key} className="font-bold text-slate-900">
          {part.slice(2, -2)}
        </strong>,
      );
    } else if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      nodes.push(
        <code key={key} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[0.9em] text-purple-700">
          {part.slice(1, -1)}
        </code>,
      );
    } else if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      nodes.push(
        <em key={key} className="italic">
          {part.slice(1, -1)}
        </em>,
      );
    } else {
      nodes.push(<React.Fragment key={key}>{part}</React.Fragment>);
    }
  });

  return nodes;
}

function splitRow(line: string): string[] {
  return line
    .replace(/^\||\|$/g, '')
    .split('|')
    .map((cell) => cell.trim());
}

const isDivider = (line: string) => /^\|?[\s:|-]+\|[\s:|-]*$/.test(line) && line.includes('-');

export default function Markdown({ source }: { source: string }) {
  const lines = source.split('\n');
  const blocks: React.ReactNode[] = [];

  let index = 0;
  let key = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    // Table: a header row followed by a |---|---| divider.
    if (trimmed.startsWith('|') && index + 1 < lines.length && isDivider(lines[index + 1].trim())) {
      const headers = splitRow(trimmed);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && lines[index].trim().startsWith('|')) {
        rows.push(splitRow(lines[index].trim()));
        index += 1;
      }
      blocks.push(
        <div key={key++} className="my-5 overflow-x-auto rounded-2xl border border-slate-200">
          <table className="w-full min-w-[20rem] border-collapse text-sm">
            <thead className="bg-slate-50">
              <tr>
                {headers.map((header, i) => (
                  <th
                    key={i}
                    className="border-b border-slate-200 px-4 py-2.5 text-left font-bold text-slate-700"
                  >
                    {renderInline(header, `th-${i}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, r) => (
                <tr key={r} className="even:bg-slate-50/50">
                  {row.map((cell, c) => (
                    <td key={c} className="border-b border-slate-100 px-4 py-2.5 text-slate-600">
                      {renderInline(cell, `td-${r}-${c}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // Heading
    const heading = /^(#{1,4})\s+(.*)$/.exec(trimmed);
    if (heading) {
      const depth = heading[1].length;
      const content = renderInline(heading[2], `h-${key}`);
      const sizes = ['text-2xl', 'text-xl', 'text-lg', 'text-base'];
      blocks.push(
        <p key={key++} className={`mt-6 mb-3 font-extrabold text-slate-800 ${sizes[depth - 1]}`}>
          {content}
        </p>,
      );
      index += 1;
      continue;
    }

    // Blockquote (consecutive lines)
    if (trimmed.startsWith('>')) {
      const quoted: string[] = [];
      while (index < lines.length && lines[index].trim().startsWith('>')) {
        quoted.push(lines[index].trim().replace(/^>\s?/, ''));
        index += 1;
      }
      blocks.push(
        <blockquote
          key={key++}
          className="my-4 rounded-r-2xl border-l-4 border-sky-300 bg-sky-50/60 py-3 pl-4 pr-3 text-slate-700"
        >
          {quoted.map((q, i) => (
            <p key={i} className="leading-relaxed">
              {renderInline(q, `bq-${key}-${i}`)}
            </p>
          ))}
        </blockquote>,
      );
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(trimmed)) {
      const items: string[] = [];
      while (index < lines.length && /^\d+\.\s/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s/, ''));
        index += 1;
        // Absorb indented continuation lines into the previous item.
        while (index < lines.length && /^\s{2,}\S/.test(lines[index]) && !/^\s*\d+\.\s/.test(lines[index])) {
          items[items.length - 1] += ` ${lines[index].trim()}`;
          index += 1;
        }
      }
      blocks.push(
        <ol key={key++} className="my-4 space-y-2 pl-1">
          {items.map((item, i) => (
            <li key={i} className="flex gap-3 leading-relaxed text-slate-600">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-bold text-sky-600">
                {i + 1}
              </span>
              <span>{renderInline(item, `ol-${key}-${i}`)}</span>
            </li>
          ))}
        </ol>,
      );
      continue;
    }

    // Unordered list
    if (/^[-*]\s/.test(trimmed)) {
      const items: string[] = [];
      while (index < lines.length && /^\s*[-*]\s/.test(lines[index])) {
        items.push(lines[index].trim().replace(/^[-*]\s/, ''));
        index += 1;
        while (index < lines.length && /^\s{2,}\S/.test(lines[index]) && !/^\s*[-*]\s/.test(lines[index])) {
          items[items.length - 1] += ` ${lines[index].trim()}`;
          index += 1;
        }
      }
      blocks.push(
        <ul key={key++} className="my-4 space-y-2 pl-1">
          {items.map((item, i) => (
            <li key={i} className="flex gap-3 leading-relaxed text-slate-600">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400" aria-hidden />
              <span>{renderInline(item, `ul-${key}-${i}`)}</span>
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    // Paragraph: gather until a blank line or the start of another block.
    const paragraph: string[] = [];
    while (index < lines.length) {
      const current = lines[index].trim();
      if (
        !current ||
        current.startsWith('|') ||
        current.startsWith('>') ||
        /^#{1,4}\s/.test(current) ||
        /^[-*]\s/.test(current) ||
        /^\d+\.\s/.test(current)
      ) {
        break;
      }
      paragraph.push(current);
      index += 1;
    }
    if (paragraph.length) {
      blocks.push(
        <p key={key++} className="my-3 leading-relaxed text-slate-600">
          {renderInline(paragraph.join(' '), `p-${key}`)}
        </p>,
      );
    }
  }

  return <div className="text-[15px]">{blocks}</div>;
}
