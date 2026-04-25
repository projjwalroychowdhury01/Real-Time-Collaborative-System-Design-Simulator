import type { DesignJSON } from '@/types/design';

/** Serialize the current design store to a plain JSON object. */
export function serializeDesign(json: DesignJSON): string {
  return JSON.stringify(json);
}

/** Parse a design JSON string into the DesignJSON shape. */
export function deserializeDesign(raw: string): DesignJSON {
  return JSON.parse(raw) as DesignJSON;
}

/** Download the current design as a .json file. */
export function downloadDesign(json: DesignJSON, name: string): void {
  const blob = new Blob([serializeDesign(json)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
