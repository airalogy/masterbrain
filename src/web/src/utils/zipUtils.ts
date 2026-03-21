import JSZip from 'jszip';
import type { FileEntry } from '../types';

function detectType(filename: string): FileEntry['type'] {
  if (filename.endsWith('.aimd')) return 'aimd';
  if (filename.endsWith('.py')) return 'py';
  return 'other';
}

export async function extractZip(file: File): Promise<FileEntry[]> {
  const zip = await JSZip.loadAsync(file);
  const entries: FileEntry[] = [];

  await Promise.all(
    Object.entries(zip.files).map(async ([path, zipEntry]) => {
      if (zipEntry.dir) return;
      const type = detectType(path);
      if (type === 'other') return;
      const content = await zipEntry.async('string');
      const name = path.split('/').pop() ?? path;
      entries.push({ name, path, content, type });
    })
  );

  return entries.sort((a, b) => a.path.localeCompare(b.path));
}

export async function packZip(files: FileEntry[]): Promise<Blob> {
  const zip = new JSZip();
  for (const f of files) {
    zip.file(f.path, f.content);
  }
  return zip.generateAsync({ type: 'blob' });
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
