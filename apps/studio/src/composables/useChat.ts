import { ref, shallowRef, type Ref, type ShallowRef } from 'vue';
import type {
  ChatMessage,
  EditorSelection,
  FileEntry,
  ModelConfig,
  ProtocolRouter,
} from '../types/index.ts';
import { DEFAULT_MODEL } from '../types/index.ts';
import {
  runCodeEdit,
  streamChatLanguage,
  streamProtocolGenV3,
  streamProtocolGenAimd,
  streamProtocolGenModel,
  streamProtocolGenAssigner,
  extractAimdBlocks,
  extractPyBlocks,
} from '../utils/apiClient.ts';

export type SendIntent = 'generate' | 'chat' | 'edit';

export function useChat(
  files: Readonly<ShallowRef<FileEntry[]>>,
  activeFile: Readonly<ShallowRef<FileEntry | null>>,
  selection: Readonly<Ref<EditorSelection | null>>,
  hasWorkspace: Readonly<Ref<boolean>>,
  onApplyContent: (content: string, type: 'aimd' | 'py') => void,
  onAutoApply: (name: string, content: string, type: 'aimd' | 'py') => void,
) {
  const messages = shallowRef<ChatMessage[]>([]);
  const isStreaming = ref(false);
  const model: Ref<ModelConfig> = ref({ ...DEFAULT_MODEL });
  const router: Ref<ProtocolRouter> = ref('v3');

  let abortFlag = false;
  let confirmResolver: ((confirmed: boolean) => void) | null = null;

  function confirmStep() {
    confirmResolver?.(true);
    confirmResolver = null;
  }

  function regenerateStep() {
    confirmResolver?.(false);
    confirmResolver = null;
  }

  function updateMessage(id: string, patch: Partial<ChatMessage>) {
    messages.value = messages.value.map(m => m.id === id ? { ...m, ...patch } : m);
  }

  async function runExplicitEditFlow(
    assistantMsgId: string,
    userMsgId: string,
    userText: string,
  ) {
    if (!hasWorkspace.value) {
      throw new Error('Select a workspace directory before using Edit mode.');
    }

    const result = await runCodeEdit({
      model: model.value,
      prompt: userText,
      files: files.value.map(file => ({
        path: file.path,
        content: file.content,
        type: file.type,
      })),
      active_file_path: activeFile.value?.path,
      selection: selection.value ? {
        text: selection.value.text,
        start_offset: selection.value.startOffset,
        end_offset: selection.value.endOffset,
      } : undefined,
      chat_history: messages.value
        .filter(msg => msg.id !== assistantMsgId && msg.id !== userMsgId)
        .map(msg => ({ role: msg.role, content: msg.content })),
    });

    const warnings = result.warnings.length > 0
      ? `\n\nWarnings:\n${result.warnings.map(w => `- ${w}`).join('\n')}`
      : '';
    const changeNotice = result.edit_status === 'changed'
      ? `\n\nPrepared ${result.changed_files.length} workspace change(s). Review them below, then click Apply or Apply all to write them into the current workspace.`
      : '';
    const noChangeNotice = result.edit_status === 'no_changes'
      ? '\n\nNo supported workspace files were changed. OpenCode ran successfully, but it either answered directly or decided no edit was needed.'
      : '';

    updateMessage(assistantMsgId, {
      content: `${result.message}${changeNotice}${noChangeNotice}${warnings}`,
      streaming: false,
      editStatus: result.edit_status,
      executionLog: result.execution_log.length > 0 ? result.execution_log : undefined,
      changedFiles: result.changed_files.length > 0 ? result.changed_files : undefined,
    });
  }

  async function sendMessage(userText: string, intent: SendIntent) {
    if (isStreaming.value || !userText.trim()) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: userText,
      intent,
    };

    messages.value = [...messages.value, userMsg];
    isStreaming.value = true;
    abortFlag = false;

    /** Stream one v1 step, auto-apply to editor, then wait for user confirm/regenerate. */
    const streamWithConfirm = async (
      label: string,
      type: 'aimd' | 'py',
      streamFn: () => AsyncGenerator<string>,
      extractFn: (raw: string) => string[],
    ): Promise<string> => {
      while (true) {
        const stepMsgId = crypto.randomUUID();
        messages.value = [...messages.value, {
          id: stepMsgId, role: 'assistant' as const,
          content: `Generating **${label}**...`, streaming: true,
        }];

        let raw = '';
        for await (const chunk of streamFn()) {
          if (abortFlag) throw new Error('aborted');
          raw += chunk;
          updateMessage(stepMsgId, { content: raw });
        }

        const blocks = extractFn(raw);
        const fileContent = blocks.length > 0 ? blocks[0] : raw.trim();

        onAutoApply(label, fileContent, type);

        updateMessage(stepMsgId, { streaming: false, content: raw, stepPending: true });

        const confirmed = await new Promise<boolean>(resolve => {
          confirmResolver = resolve;
        });

        if (confirmed) {
          updateMessage(stepMsgId, { stepPending: false });
          return fileContent;
        } else {
          updateMessage(stepMsgId, { stepPending: false, content: raw + '\n\n🔄 *Regenerating...*' });
        }
      }
      throw new Error('unreachable');
    };

    try {
      if ((intent === 'generate' || intent === 'edit') && !hasWorkspace.value) {
        throw new Error('Select a workspace directory before generating or editing files.');
      }

      if (intent === 'generate' && router.value === 'v1') {
        const aimdContent = await streamWithConfirm(
          'protocol.aimd', 'aimd',
          () => streamProtocolGenAimd({ use_model: model.value, instruction: userText }),
          extractAimdBlocks,
        );

        const modelContent = await streamWithConfirm(
          'model.py', 'py',
          () => streamProtocolGenModel({ use_model: model.value, protocol_aimd: aimdContent }),
          extractPyBlocks,
        );

        await streamWithConfirm(
          'assigner.py', 'py',
          () => streamProtocolGenAssigner({ use_model: model.value, protocol_aimd: aimdContent, protocol_model: modelContent }),
          extractPyBlocks,
        );

      } else if (intent === 'generate') {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(), role: 'assistant', content: '', streaming: true,
        };
        messages.value = [...messages.value, assistantMsg];

        let fullContent = '';
        for await (const chunk of streamProtocolGenV3({ use_model: model.value, instruction: userText })) {
          if (abortFlag) break;
          fullContent += chunk;
          updateMessage(assistantMsg.id, { content: fullContent });
        }

        const aimdBlocks = extractAimdBlocks(fullContent);
        const aimdContent = aimdBlocks.length > 0 ? aimdBlocks[0] : fullContent.trim();
        if (aimdContent) onAutoApply('protocol.aimd', aimdContent, 'aimd');

        updateMessage(assistantMsg.id, {
          streaming: false,
          content: fullContent + (aimdContent ? '\n\n✅ **protocol.aimd** written to editor' : ''),
        });

      } else if (intent === 'edit') {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(), role: 'assistant', content: '', streaming: true,
        };
        messages.value = [...messages.value, assistantMsg];

        await runExplicitEditFlow(assistantMsg.id, userMsg.id, userText);
      } else {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(), role: 'assistant', content: '', streaming: true,
        };
        messages.value = [...messages.value, assistantMsg];

        const contextMessages: Array<{ role: string; content: string }> = [];
        const file = activeFile.value;
        if (file) {
          contextMessages.push({
            role: 'user',
            content: `Current file (${file.name}):\n\`\`\`${file.type === 'aimd' ? 'aimd' : 'python'}\n${file.content}\n\`\`\``,
          });
          contextMessages.push({
            role: 'assistant',
            content: 'I can see the current file. How can I help you modify or improve it?',
          });
        }
        for (const msg of messages.value) {
          if (msg.id !== assistantMsg.id && msg.id !== userMsg.id) {
            contextMessages.push({ role: msg.role, content: msg.content });
          }
        }
        contextMessages.push({ role: 'user', content: userText });

        let fullContent = '';
        for await (const chunk of streamChatLanguage({ model: model.value, messages: contextMessages })) {
          if (abortFlag) break;
          fullContent += chunk;
          updateMessage(assistantMsg.id, { content: fullContent });
        }

        const aimdBlocks = extractAimdBlocks(fullContent);
        const pyBlocks = extractPyBlocks(fullContent);
        const allBlocks: string[] = [
          ...aimdBlocks,
          ...pyBlocks.map(b => `__py__${b}`),
        ];

        updateMessage(assistantMsg.id, {
          content: fullContent,
          streaming: false,
          aimdBlocks: allBlocks.length > 0 ? allBlocks : undefined,
        });
      }
    } catch (err) {
      if (err instanceof Error && err.message === 'aborted') {
        // silently ignore
      } else {
        const errMsg = err instanceof Error ? err.message : 'Unknown error';
        const lastMsg = messages.value[messages.value.length - 1];
        if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
          updateMessage(lastMsg.id, { content: `❌ Error: ${errMsg}`, streaming: false });
        } else {
          messages.value = [...messages.value, {
            id: crypto.randomUUID(), role: 'assistant' as const,
            content: `❌ Error: ${errMsg}`, streaming: false,
          }];
        }
      }
    } finally {
      isStreaming.value = false;
      confirmResolver = null;
    }
  }

  function applyBlock(block: string) {
    if (block.startsWith('__py__')) {
      onApplyContent(block.slice(6), 'py');
    } else {
      onApplyContent(block, 'aimd');
    }
  }

  function dismissBlock(msgId: string) {
    messages.value = messages.value.map(m =>
      m.id === msgId ? { ...m, aimdBlocks: undefined } : m
    );
  }

  function removeChangedFile(msgId: string, path: string) {
    messages.value = messages.value.map(m => {
      if (m.id !== msgId || !m.changedFiles) return m;
      const remaining = m.changedFiles.filter(change => change.path !== path);
      return { ...m, changedFiles: remaining.length > 0 ? remaining : undefined };
    });
  }

  function dismissChangedFiles(msgId: string) {
    messages.value = messages.value.map(m =>
      m.id === msgId ? { ...m, changedFiles: undefined } : m
    );
  }

  function clearMessages() {
    messages.value = [];
  }

  return {
    messages,
    isStreaming,
    model,
    router,
    sendMessage,
    applyBlock,
    dismissBlock,
    removeChangedFile,
    dismissChangedFiles,
    clearMessages,
    confirmStep,
    regenerateStep,
  };
}
