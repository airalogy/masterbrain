import type { App, ComputedRef, InjectionKey, MaybeRefOrGetter } from 'vue';
import { computed, inject, provide, toValue } from 'vue';

export const MASTERBRAIN_SUPPORTED_LOCALES = ['en-US', 'zh-CN'] as const;

export type MasterbrainLocale = typeof MASTERBRAIN_SUPPORTED_LOCALES[number];

export interface MasterbrainMessages {
  changeStatus: {
    applied: string;
    viewChanges: string;
    undo: string;
    undoing: string;
  };
  changeReview: {
    title: string;
    summary: string;
    technicalDiff: string;
    close: string;
    applyChanges: string;
    applying: string;
    safeHint: string;
    reviewHint: string;
    fileCount: string;
    safe: string;
    warning: string;
    destructive: string;
    created: string;
    modified: string;
    deleted: string;
  };
  diff: {
    details: string;
    modeHint: string;
    inline: string;
    sideBySide: string;
    fallback: string;
  };
  files: {
    aimd: string;
    model: string;
    assigner: string;
    toml: string;
  };
  fileSummary: {
    created: string;
    modified: string;
    deleted: string;
  };
  common: {
    warnings: string;
    executionLog: string;
  };
}

export type DeepPartial<T> = {
  [Key in keyof T]?: T[Key] extends object ? DeepPartial<T[Key]> : T[Key];
};

export type MasterbrainMessageOverrides = Partial<Record<MasterbrainLocale, DeepPartial<MasterbrainMessages>>>;
export type MasterbrainMessageParams = Record<string, string | number>;

type LeafPaths<T> = {
  [Key in keyof T & string]: T[Key] extends string
    ? Key
    : T[Key] extends object
      ? `${Key}.${LeafPaths<T[Key]>}`
      : never;
}[keyof T & string];

export type MasterbrainMessageKey = LeafPaths<MasterbrainMessages>;

export interface MasterbrainI18nOptions {
  locale?: MaybeRefOrGetter<string | null | undefined>;
  messages?: MaybeRefOrGetter<MasterbrainMessageOverrides | null | undefined>;
}

export interface MasterbrainI18n {
  locale: ComputedRef<MasterbrainLocale>;
  messages: ComputedRef<MasterbrainMessages>;
  t: (key: MasterbrainMessageKey, params?: MasterbrainMessageParams) => string;
}

export interface MasterbrainI18nPlugin extends MasterbrainI18n {
  install: (app: App) => void;
}

const EN_US_MESSAGES: MasterbrainMessages = {
  changeStatus: {
    applied: 'AI changes applied',
    viewChanges: 'View changes',
    undo: 'Undo',
    undoing: 'Undoing…',
  },
  changeReview: {
    title: 'Review AI changes',
    summary: 'Change summary',
    technicalDiff: 'Technical diff',
    close: 'Close',
    applyChanges: 'Apply changes',
    applying: 'Applying…',
    safeHint: 'The change set passed deterministic checks.',
    reviewHint: 'This change set needs your attention before it is applied.',
    fileCount: '{count} file(s)',
    safe: 'Safe',
    warning: 'Warning',
    destructive: 'Destructive',
    created: 'Created',
    modified: 'Modified',
    deleted: 'Deleted',
  },
  diff: {
    details: 'View detailed differences',
    modeHint: 'Line changes are highlighted below',
    inline: 'Inline',
    sideBySide: 'Side by side',
    fallback: 'No diff is available.',
  },
  files: {
    aimd: 'Experimental flow and record fields',
    model: 'Data model and validation',
    assigner: 'Automatic calculation rules',
    toml: 'Protocol information',
  },
  fileSummary: {
    created: 'Created {file} with {added} added line(s).',
    modified: 'Updated {file}: {added} line(s) added and {removed} line(s) removed.',
    deleted: 'Deleted {file}, removing {removed} line(s).',
  },
  common: {
    warnings: 'Warnings',
    executionLog: 'Execution log',
  },
};

const ZH_CN_MESSAGES: MasterbrainMessages = {
  changeStatus: {
    applied: '已自动应用 AI 修改',
    viewChanges: '查看变更',
    undo: '撤销',
    undoing: '正在撤销…',
  },
  changeReview: {
    title: '审核 AI 修改',
    summary: '变更摘要',
    technicalDiff: '技术差异',
    close: '关闭',
    applyChanges: '应用变更',
    applying: '正在应用…',
    safeHint: '这组变更已通过确定性检查。',
    reviewHint: '这组变更需要确认后才能应用。',
    fileCount: '{count} 个文件',
    safe: '安全',
    warning: '警告',
    destructive: '破坏性变更',
    created: '已新建',
    modified: '已修改',
    deleted: '已删除',
  },
  diff: {
    details: '查看详细差异',
    modeHint: '下方已高亮具体行变更',
    inline: '行内对比',
    sideBySide: '左右对比',
    fallback: '暂无可显示的差异。',
  },
  files: {
    aimd: '实验流程与记录字段',
    model: '数据模型与校验',
    assigner: '自动计算规则',
    toml: 'Protocol 基本信息',
  },
  fileSummary: {
    created: '新建 {file}，新增 {added} 行内容。',
    modified: '更新 {file}：新增 {added} 行，删除 {removed} 行。',
    deleted: '删除 {file}，共移除 {removed} 行内容。',
  },
  common: {
    warnings: '警告',
    executionLog: '执行日志',
  },
};

export const MASTERBRAIN_MESSAGES: Readonly<Record<MasterbrainLocale, MasterbrainMessages>> = {
  'en-US': EN_US_MESSAGES,
  'zh-CN': ZH_CN_MESSAGES,
};

interface MasterbrainI18nContext extends MasterbrainI18n {
  overrides: ComputedRef<MasterbrainMessageOverrides>;
}

const MASTERBRAIN_I18N_KEY: InjectionKey<MasterbrainI18nContext> = Symbol('masterbrain-i18n');

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function mergeObjects<T extends object>(base: T, override?: DeepPartial<T> | null): T {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(base)) {
    result[key] = isObject(value) ? mergeObjects(value) : value;
  }
  if (!override) return result as T;
  for (const [key, value] of Object.entries(override)) {
    const baseValue = result[key];
    result[key] = isObject(baseValue) && isObject(value)
      ? mergeObjects(baseValue, value)
      : value;
  }
  return result as T;
}

function mergeOverrides(
  base?: MasterbrainMessageOverrides | null,
  override?: MasterbrainMessageOverrides | null,
): MasterbrainMessageOverrides {
  return {
    'en-US': mergeObjects(base?.['en-US'] ?? {}, override?.['en-US']),
    'zh-CN': mergeObjects(base?.['zh-CN'] ?? {}, override?.['zh-CN']),
  };
}

export function resolveMasterbrainLocale(
  locale?: string | null,
  fallback: MasterbrainLocale = 'en-US',
): MasterbrainLocale {
  if (!locale) return fallback;
  const normalized = locale.replace('_', '-').toLowerCase();
  if (normalized === 'zh' || normalized.startsWith('zh-')) return 'zh-CN';
  if (normalized === 'en' || normalized.startsWith('en-')) return 'en-US';
  return fallback;
}

export function createMasterbrainMessages(
  locale?: string | null,
  overrides?: MasterbrainMessageOverrides | null,
): MasterbrainMessages {
  const resolvedLocale = resolveMasterbrainLocale(locale);
  return mergeObjects(MASTERBRAIN_MESSAGES[resolvedLocale], overrides?.[resolvedLocale]);
}

export function translateMasterbrainMessage(
  messages: MasterbrainMessages,
  key: MasterbrainMessageKey,
  params: MasterbrainMessageParams = {},
): string {
  const value = key.split('.').reduce<unknown>((current, segment) => {
    return isObject(current) ? current[segment] : undefined;
  }, messages);
  if (typeof value !== 'string') return key;
  return value.replace(/\{([^}]+)\}/g, (placeholder, name: string) => {
    const replacement = params[name];
    return replacement === undefined ? placeholder : String(replacement);
  });
}

function createContext(
  options: MasterbrainI18nOptions = {},
  parent?: MasterbrainI18nContext | null,
): MasterbrainI18nContext {
  const locale = computed(() => {
    const requested = options.locale === undefined ? undefined : toValue(options.locale);
    return resolveMasterbrainLocale(requested, parent?.locale.value ?? 'en-US');
  });
  const overrides = computed(() => {
    const local = options.messages === undefined ? undefined : toValue(options.messages);
    return mergeOverrides(parent?.overrides.value, local);
  });
  const messages = computed(() => createMasterbrainMessages(locale.value, overrides.value));
  return {
    locale,
    overrides,
    messages,
    t: (key, params) => translateMasterbrainMessage(messages.value, key, params),
  };
}

export function createMasterbrainI18n(options: MasterbrainI18nOptions = {}): MasterbrainI18nPlugin {
  const context = createContext(options);
  return {
    ...context,
    install(app) {
      app.provide(MASTERBRAIN_I18N_KEY, context);
    },
  };
}

export function provideMasterbrainI18n(options: MasterbrainI18nOptions = {}): MasterbrainI18n {
  const context = createContext(options, inject(MASTERBRAIN_I18N_KEY, null));
  provide(MASTERBRAIN_I18N_KEY, context);
  return context;
}

export function useMasterbrainI18n(options: MasterbrainI18nOptions = {}): MasterbrainI18n {
  return createContext(options, inject(MASTERBRAIN_I18N_KEY, null));
}
