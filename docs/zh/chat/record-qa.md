# AI-assisted QA with Airalogy Records

## 数据结构设计理念

在AI对话中，我们经常遇到这样一种情况：

用户在刚开始的对话，没有选择任何Airalogy Records，但在对话的某一轮中，用户选择了一系列Records，并提出了问题。这时，我们需要将这些Records注入到对话中。用户可能后续会基于当前Records提出多轮问题，之后再选择其他Records，再提出问题，如此往复。此外，本对话设计也同时兼容注入不同Units中的Discussions。

为此，本设计结构的目标是支持上述场景。

## 基本数据结构

该AI Chat的数据结构也兼容[基本的对话数据结构](data-structure.md)，请先阅读理解后方能继续。

## Functions

本数据结构的核心设计在于通过构造，具有特定结构的不同Function，作为Tool的调用来实现。这些Functions本质都是Airalogy网站的后端进行构造。

### `inject_airalogy_protocols`

Arguments:

需注意，Function的Arguments通常要求是一个JSON Object的字符串化形式，也就是必须是字典形式的字符串，而不能是列表形式的字符串。因此，后续所有Function的Arguments都是这种形式。

```json
{
    "airalogy_protocol_ids": [
        "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
        "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
    ]
}
```

Content:

```json
{
    "airalogy_protocols": [
        {
            "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
            "markdown": "stringified protocol.aimd",  // Airalogy Protocol的核心文本内容主要定义于Airalogy Protocol Model中，这里只需要将其字符串化传入即可帮助LLM理解
            "field_json_schema": { // 进一步帮助LLM理解Airalogy Protocol Markdown中的各个数据字段的含义
                // Airalogy Protocol Field JSON Schema. 基于Airalogy Protocol Model获得。不需要将原始JSON Schema字符串化，直接放入对象即可
            }
        },
        {
            "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
            "markdown": "stringified protocol.aimd",
            "field_json_schema": {
                // ...
            }
        }
    ]
}
```

### `inject_airalogy_records`

Arguments:

```json
{
    "airalogy_record_ids": [
        "airalogy.id.record.550e8400-e29b-41d4-a716-446655440001.v.1",
        "airalogy.id.record.123e4567-e89b-12d3-a456-426614174002.v.1",
    ]
}
```

Content:

```json
{
    "airalogy_records": [
        // 即把原始的Airalogy Records的JSON注入即可
        {
            "airalogy_record_id": "airalogy.id.record.550e8400-e29b-41d4-a716-446655440001.v.1",
            "metadata": {
                "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1", // 必须要有这个字段，用于帮助LLM理解该Record是基于哪个Protocol的
                // ...
            },
            "data": {
                "var": {
                    // ...
                },
                "step": {
                    // ...
                },
                "check": {
                    // ...
                }
            }
        },
        {
            "airalogy_record_id": "airalogy.id.record.123e4567-e89b-12d3-a456-426614174002",
            "metadata": {
                "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
                // ...
            },
            "data": {
                // ...
            }
        },
        // ...
    ]
}
```

### `inject_airalogy_discussions`

Arguments:

```json
{
    "airalogy_discussion_ids": [
        "airalogy.id.discussion.550e8400-e29b-41d4-a716-446655440001",
        "airalogy.id.discussion.123e4567-e89b-12d3-a456-426614174002",
        "airalogy.id.discussion.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyy1",
    ]
}
```

Content:

```json
{
    "airalogy_discussions": [
        {
            "airalogy_discussion_id": "airalogy.id.discussion.550e8400-e29b-41d4-a716-446655440001",
            "content": "str", // 即把搜索到的Discussion的内容注入即可
            // 这里实际上可以加其他的字段，比如similarity等
        },
        {
            "airalogy_discussion_id": "airalogy.id.discussion.123e4567-e89b-12d3-a456-426614174002",
            "content": "str",
        },
        {
            "airalogy_discussion_id": "airalogy.id.discussion.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyy1",
            "content": "str",
        }
    ]
}
```

## 对话结构设计

在Record QA中，我们主要需要通过改变`context`和`main_messages`来帮助管理数据和辅助前端展示。

### 情况1：第一轮无Record注入的对话

当用户在任意Airalogy Protocol界面中打开AI Chat，并进行第一轮提问时，Airalogy Masterbrain总会将当前Airalogy Protocol的信息注入，具体包括Airalogy Protocol Markdown和Airalogy Protocol Field JSON Schema。

```json
{
    "context": {
        "inject_airalogy_protocols": {
            "enabled": true,
            "airalogy_protocol_ids": [
                "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
                // 这里可以是任意一个Airalogy Protocol的ID
                // 也可以是多个Protocol的ID
            ]
        }
    },
    "main_messages": [
        {
            "role": "user",
            "content": "请解释这个Airalogy Protocol。"
        },


        // 前端构造如下AT消息
        // #####################################################################
        // A
        {
            "role": "assistant",
            "content": "", // 这里也可以是null，但为了兼容不同模型，我们保留空字符串
            "tool_calls": [
                {
                    "id": "call_abc123", // 一个随机生成的ID，用于标识这次调用
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_protocols",
                        "arguments": "<info_of_protocols_for_injection>"
                    }
                }
            ]
        },
        // T
        {
            "role": "tool",
            "content": "<data_of_injected_protocols>", 
            "tool_call_id": "call_abc123"
        },
        // #####################################################################

        {
            "role": "assistant",
            "content": "该Protocol是..."
        }
    ]
}
```

`<info_of_protocols_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocol_ids": [
        "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1"
    ]
}
```

`<data_of_injected_protocols>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocols": [
        {
            "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
            "markdown": "stringified protocol.aimd", // Airalogy Protocol的核心文本内容主要定义于Airalogy Protocol Model中，这里只需要将其字符串化传入即可帮助LLM理解
            "field_json_schema": { // 进一步帮助LLM理解Airalogy Protocol Markdown中的各个数据字段的含义
                // Airalogy Protocol Field JSON Schema. 基于Airalogy Protocol Model获得。不需要将原始JSON Schema字符串化，直接放入对象即可
            }
        }
    ]
}
```

这种设计的额外好处是，兼容多个Protocol的注入。例如：

```json
{
    "context": {
        "inject_airalogy_protocols": {
            "enabled": true,
            "airalogy_protocol_ids": [
                "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
                "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
            ]
        }
    },
    "main_messages": [
        {
            "role": "user",
            "content": "请说明这2个Airalogy Protocols的区别。"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_protocols",
                        "arguments": "<info_of_protocols_for_injection>"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "<data_of_injected_protocols>", 
            "tool_call_id": "call_abc123"
        },
        {
            "role": "assistant",
            "content": "这2个Protocols的区别是..."
        }
    ]
}
```

`<context_info>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocol_ids": [
        "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
        "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
    ]
}
```

`<data_of_injected_protocols>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocols": [
        {
            "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol1.v.0.0.1",
            "markdown": "stringified protocol.aimd",
            "field_json_schema": {
                // ...
            }
        },
        {
            "airalogy_protocol_id": "airalogy.id.lab.lab1.project.project1.protocol.protocol2.v.0.0.1",
            "markdown": "stringified protocol.aimd",
            "field_json_schema": {
                // ...
            }
        }
    ]   
}
```

### 情况2：第一轮有Record(s)注入的对话

当然，用户在第一轮对话中也可以选择Records，这时，我们需要将Records注入到对话中。注意，为了理解一个Airalogy Record，我们必须同时把其对应的Airalogy Protocol也注入。

```json
{
    "context": {
        "inject_airalogy_protocols": {
            "enabled": true,
            "airalogy_protocol_ids": [
                "<protocol_id_1>",
            ]
        },
        "inject_airalogy_records": {
            "enabled": true,
            "airalogy_record_ids": [
                "<record_id_1_from_protocol_id_1>",
                "<record_id_2_from_protocol_id_1>",
            ]
        }
    },
    "main_messages": [
        {
            "role": "user",
            "content": "这2个Records有什么不同？"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_protocols",
                        "arguments": "<info_of_protocols_for_injection>"
                    }
                },
                {
                    "id": "call_def456", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_records",
                        "arguments": "<info_of_records_for_injection>"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "<data_of_injected_protocols>",
            "tool_call_id": "call_abc123"
        },
        {
            "role": "tool",
            "content": "<data_of_injected_records>",
            "tool_call_id": "call_def456"
        },
        {
            "role": "assistant",
            "content": "这2个Records的不同是..."
        }
    ]
}
```

`<info_of_protocols_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocol_ids": [
        "<protocol_id_1>"
    ]
}
```

`<data_of_injected_protocols>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocols": [
        {
            "airalogy_protocol_id": "<protocol_id_1>",
            "markdown": "stringified protocol.aimd",
            "field_json_schema": {
                // ...
            }
        }
    ]
}
```

`<info_of_records_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_record_ids": [
        "<record_id_1_from_protocol_id_1>",
        "<record_id_2_from_protocol_id_1>",
    ]
}
```

`<data_of_injected_records>`为如下JSON的字符串化形式：

```json
{
    "airalogy_records": [
        {
            "airalogy_record_id": "<record_id_1_from_protocol_id_1>",
            "metadata": {
                "airalogy_protocol_id": "<protocol_id_1>"
                // ...
            },
            "data": {
                "var": {
                    // ...
                },
                "step": {
                    // ...
                },
                "check": {
                    // ...
                }
            }
        },
        {
            "airalogy_record_id": "<record_id_2_from_protocol_id_1>",
            "metadata": {
                "airalogy_protocol_id": "<protocol_id_1>"
                // ...
            },
            "data": {
                // ...
            }
        }
    ]
}
```

如果注入的Records是基于不同的Protocol，那么`<data_of_injected_records>`中的`metadata`字段中的`airalogy_protocol_id`字段应该对应不同的Protocol。

### 情况3：第一轮无Record注入，后续轮有Record(s)注入的对话

在后续轮中，用户可能会选择不同的Records，这时，我们需要将新Records注入到对话中。注意，为了理解一个Airalogy Record，我们必须同时把其对应的Airalogy Protocol也注入。

```json
{
    "context": {
        "inject_airalogy_protocols": {
            "enabled": true,
            "airalogy_protocol_ids": [
                "<protocol_id_1>",
            ]
        },
        "inject_airalogy_records": {
            "enabled": true,
            "airalogy_record_ids": [
                "<record_id_1_from_protocol_id_1>",
                "<record_id_2_from_protocol_id_1>",
            ]
        }
    },
    "main_messages": [
        {
            "role": "user",
            "content": "解释这个Protocol。"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_protocols",
                        "arguments": "<info_of_protocols_for_injection>"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "<data_of_injected_protocols>",
            "tool_call_id": "call_abc123"
        },
        {
            "role": "assistant",
            "content": "这个Protocol是..."
        },
        {
            "role": "user",
            "content": "这2个Records有什么不同？"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_def456", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_records",
                        "arguments": "<info_of_records_for_injection>"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "<data_of_injected_records>",
            "tool_call_id": "call_def456"
        },
        {
            "role": "assistant",
            "content": "这2个Records的不同是..."
        }
    ]
}
```

`<info_of_protocols_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocol_ids": [
        "<protocol_id_1>"
    ]
}
```

`<data_of_injected_protocols>`为如下JSON的字符串化形式：

```json
{
    "airalogy_protocols": [
        {
            "airalogy_protocol_id": "<protocol_id_1>",
            "markdown": "stringified protocol.aimd",
            "field_json_schema": {
                // ...
            }
        }
    ]
}
```

`<info_of_records_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_record_ids": [
        "<record_id_1_from_protocol_id_1>",
        "<record_id_2_from_protocol_id_1>",
    ]
}
```

`<data_of_injected_records>`为如下JSON的字符串化形式：

```json
{
    "airalogy_records": [
        {
            "airalogy_record_id": "<record_id_1_from_protocol_id_1>",
            "metadata": {
                "airalogy_protocol_id": "<protocol_id_1>"
                // ...
            },
            "data": {
                "var": {
                    // ...
                },
                "step": {
                    // ...
                },
                "check": {
                    // ...
                }
            }
        },
        {
            "airalogy_record_id": "<record_id_2_from_protocol_id_1>",
            "metadata": {
                "airalogy_protocol_id": "<protocol_id_1>"
                // ...
            },
            "data": {
                // ...
            }
        }
    ]
}
```

### 扩展情况1：在对话中还包含Discussions

```json
{
    "context": {
        "inject_airalogy_protocols": {
            "enabled": true,
            "airalogy_protocol_ids": [
                "<protocol_id_1>",
            ]
        },
        "inject_airalogy_records": {
            "enabled": true,
            "airalogy_record_ids": [
                "<record_id_1_from_protocol_id_1>",
                "<record_id_2_from_protocol_id_1>",
            ]
        },
        "inject_airalogy_discussions": {
            "enabled": true,
            "scope": "protocol", // 该字段仅作示意，可以用于控制注入的Discussion的搜索范围，比如`protocol`表示只搜索与当前Protocol下的Discussions。其他还可以有`project`、`lab`, `public`等
            "airalogy_discussion_ids": [
                "<discussion_id_1>",
                "<discussion_id_2>",
            ]
        }
    },
    "main_messages": [
        {
            "role": "user",
            "content": "这2个Records有什么不同？Discussions部分有没有相关内容？"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_abc123", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_protocols",
                        "arguments": "<info_of_protocols_for_injection>"
                    }
                },
                {
                    "id": "call_def456", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_records",
                        "arguments": "<info_of_records_for_injection>"
                    }
                },
                {
                    "id": "call_ghi789", 
                    "type": "function",
                    "function": {
                        "name": "inject_airalogy_discussions",
                        "arguments": "<info_of_discussions_for_injection>"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "<data_of_injected_protocols>",
            "tool_call_id": "call_abc123"
        },
        {
            "role": "tool",
            "content": "<data_of_injected_records>",
            "tool_call_id": "call_def456"
        },
        {
            "role": "tool",
            "content": "<data_of_injected_discussions>",
            "tool_call_id": "call_ghi789"
        },
        {
            "role": "assistant",
            "content": "这2个Records的不同是...Discussions部分提到..."
        }
    ]
}
```

`<info_of_discussions_for_injection>`为如下JSON的字符串化形式：

```json
{
    "airalogy_discussion_ids": [
        "<discussion_id_1>",
        "<discussion_id_2>",
    ]
}
```

`<data_of_injected_discussions>`为如下JSON的字符串化形式：

```json
{
    "airalogy_discussions": [
        {
            "airalogy_discussion_id": "<discussion_id_1>",
            "content": "str", // 即把搜索到的Discussion的内容注入即可
            // 这里实际上可以加其他的字段，比如similarity等
        },
        {
            "airalogy_discussion_id": "<discussion_id_2>",
            "content": "str",
        }
    ]
}
```
