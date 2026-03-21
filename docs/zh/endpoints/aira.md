# Endpoint: AIRA

在本Endpoint中，提供了与通用AI科研自动化 (AI Research Automation, AIRA) 方法相关的实现。AIRA方法旨在通过AI技术自动化科研过程中的各个环节，提高科研效率和质量。其包含6个关键AI方法

- AI方法1：生成研究目标 (Generate Research Goal)
- AI方法2：生成研究策略 (Generate Research Strategy)
- AI方法3：选择下一个Airalogy Protocol (Select Next Airalogy Protocol)
- AI方法4：为下一个Protocol生成字段值 (Generate Values for Fields in Next Protocol)
- AI方法5：生成阶段性研究结论 (Generate Phased Research Conclusion)
- AI方法6：生成最终研究结论 (Generate Final Research Conclusion)

在代码结构中，各个方法被组织到`endpoints/aira/logic/functions/`目录下。每个方法对应一个Python文件，文件名与方法名称一致。这样可以清晰地组织和管理各个方法的实现逻辑。

也即：

```txt
masterbrain/
├── endpoints/
│   ├── aira/
│   │   ├── types.py
│   │   ├── router.py
│   │   ├── logic/
│   │   │   ├── functions/
│   │   │   │   ├── generate_goal/
│   │   │   │   ├── generate_strategy/
│   │   │   │   ├── select_protocol/
│   │   │   │   ├── generate_values/
│   │   │   │   ├── generate_phased_conclusion/
│   │   │   │   ├── generate_final_conclusion/
...
```

## 数据结构

AIRA方法的数据结构主要包括以下几个部分：

```json
{
    "workflow_info": {
        // 工作流相关信息
    },
    "protocols_info": {
        // Protocols相关信息
    },
    "path_data": {
        "path_status": "<current_status>",
        "steps": [
            {
                // 该Step的数据
            },
            {
                // 该Step的数据
            }
            // ...
        ]
    }
}
```

由于AIRA方法本质上是将上述6个关键AI方法按顺序调用（有的AI方法只能使用1次，有的可以多次）。因此在实现过程中，我们设计为维护一个`path_data`对象来跟踪当前的工作流状态和步骤。此外，在每次AI端接收到JSON时，我们会读取`path_data.path_status`来确定当前的状态，并根据该状态执行相应的过程。当该步骤执行完毕后，我们会更新`path_data.path_status`为下一个状态，并在`path_data.steps`中增加一个新的步骤记录。因此，本质上当一个Workflow通过AIRA方法执行完毕后，`path_data.steps`中会包含所有步骤的记录和数据。
