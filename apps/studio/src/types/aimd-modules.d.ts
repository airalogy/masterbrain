declare module '@airalogy/aimd-editor/monaco' {
  import type * as Monaco from 'monaco-editor';

  export const language: Monaco.languages.IMonarchLanguage;
  export const conf: Monaco.languages.LanguageConfiguration;
  export const completionItemProvider: Monaco.languages.CompletionItemProvider;
  export const aimdTokenColors: Array<{
    scope: string | string[];
    settings: {
      foreground?: string;
      fontStyle?: string;
    };
  }>;
}

declare module '@airalogy/aimd-renderer' {
  export type AimdAssignerVisibility = 'hidden' | 'collapsed' | 'expanded';

  export interface AimdRendererOptions {
    assignerVisibility?: AimdAssignerVisibility;
    groupStepBodies?: boolean;
    groupCheckBodies?: boolean;
    locale?: string;
  }

  export interface RenderToHtmlResult {
    html: string;
    fields: unknown;
  }

  export function renderToHtml(
    source: string,
    options?: AimdRendererOptions,
  ): Promise<RenderToHtmlResult>;
}

declare module '@airalogy/aimd-recorder/styles';
declare module '@airalogy/aimd-renderer/styles';
