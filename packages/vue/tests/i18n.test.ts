import type { AppliedChangeSet, CodeEditResponse } from '@airalogy/masterbrain-client';
import { createSSRApp, defineComponent, h, ref } from 'vue';
import { renderToString } from '@vue/server-renderer';
import { describe, expect, it } from 'vitest';
import MasterbrainChangeReview from '../src/MasterbrainChangeReview.vue';
import MasterbrainChangeStatus from '../src/MasterbrainChangeStatus.vue';
import MasterbrainI18nProvider from '../src/MasterbrainI18nProvider.vue';
import {
  createMasterbrainI18n,
  createMasterbrainMessages,
  resolveMasterbrainLocale,
  translateMasterbrainMessage,
} from '../src/i18n.js';

const response: CodeEditResponse = {
  runtime: 'opencode',
  contract_version: '1',
  outcome: 'changed',
  change_set_id: `sha256:${'c'.repeat(64)}`,
  message: 'Changed the title.',
  edit_status: 'changed',
  changed_files: [{
    path: 'protocol.aimd',
    name: 'protocol.aimd',
    type: 'aimd',
    status: 'modified',
    content: '# After',
    diff: '-# Before\n+# After',
    before_hash: `sha256:${'a'.repeat(64)}`,
    after_hash: `sha256:${'b'.repeat(64)}`,
  }],
  warnings: [],
  execution_log: [],
  risk: { level: 'safe', reasons: [], recommended_action: 'auto_apply' },
};

const applied: AppliedChangeSet = {
  id: response.change_set_id,
  response,
  files: [{
    path: 'protocol.aimd',
    type: 'aimd',
    before: { path: 'protocol.aimd', type: 'aimd', content: '# Before' },
    beforeHash: response.changed_files[0]?.before_hash ?? null,
    afterHash: response.changed_files[0]?.after_hash ?? null,
  }],
};

describe('Masterbrain i18n', () => {
  it('normalizes supported language variants and falls back to English', () => {
    expect(resolveMasterbrainLocale('zh_CN')).toBe('zh-CN');
    expect(resolveMasterbrainLocale('zh-Hans')).toBe('zh-CN');
    expect(resolveMasterbrainLocale('en-GB')).toBe('en-US');
    expect(resolveMasterbrainLocale('fr-FR')).toBe('en-US');
  });

  it('interpolates messages and applies locale-specific overrides with built-in fallback', () => {
    const messages = createMasterbrainMessages('zh-CN', {
      'zh-CN': { changeStatus: { viewChanges: '查看这次修改' } },
    });
    expect(messages.changeStatus.viewChanges).toBe('查看这次修改');
    expect(messages.changeStatus.undo).toBe('撤销');
    expect(translateMasterbrainMessage(messages, 'changeReview.fileCount', { count: 3 })).toBe('3 个文件');
  });

  it('reacts to host locale changes through the installable i18n bridge', () => {
    const locale = ref('en-US');
    const i18n = createMasterbrainI18n({ locale });
    expect(i18n.t('changeStatus.undo')).toBe('Undo');
    locale.value = 'zh-CN';
    expect(i18n.t('changeStatus.undo')).toBe('撤销');
  });

  it('provides localization once through the Vue application plugin', async () => {
    const app = createSSRApp({
      render: () => h(MasterbrainChangeStatus, { applied }),
    });
    app.use(createMasterbrainI18n({ locale: 'zh-CN' }));
    expect(await renderToString(app)).toContain('查看变更');
  });

  it('renders review and status primitives in Chinese from one provider', async () => {
    const Root = defineComponent(() => () => h(MasterbrainI18nProvider, { locale: 'zh-CN' }, {
      default: () => [
        h(MasterbrainChangeStatus, { applied }),
        h(MasterbrainChangeReview, { result: response }),
      ],
    }));
    const html = await renderToString(createSSRApp(Root));
    expect(html).toContain('已自动应用 AI 修改');
    expect(html).toContain('查看变更');
    expect(html).toContain('审核 AI 修改');
    expect(html).toContain('1 个文件');
    expect(html).toContain('已修改');
  });

  it('keeps legacy label props as the highest-priority override', async () => {
    const html = await renderToString(createSSRApp({
      render: () => h(MasterbrainChangeStatus, {
        applied,
        locale: 'zh-CN',
        undoLabel: 'Revert now',
      }),
    }));
    expect(html).toContain('Revert now');
    expect(html).toContain('查看变更');
  });
});
