# AIRA Endpoint

`POST /api/endpoints/aira` 实现的是 AIRA，即 AI Research Automation。

## 它做什么

这个 endpoint 会根据当前工作流状态，执行结构化科研流程中的下一步。

当前路由会在 6 个核心 AI 方法之间分发：

1. 生成研究目标
2. 生成研究策略
3. 选择下一个 protocol
4. 为下一个 protocol 生成初始字段值
5. 生成阶段性研究结论
6. 生成最终研究结论

## 分发方式

后端会读取 `workflow_data.path_data.path_status`，并根据该状态决定调用哪个函数。

当前状态包括：

- `waiting_for_research_goal`
- `waiting_for_research_strategy`
- `waiting_for_next_protocol`
- `waiting_for_initial_values_for_fields_in_next_protocol`
- `waiting_for_phased_research_conclusion`
- `waiting_for_final_research_conclusion`

每一步成功执行后，都会返回一个结构化状态变更对象，用于补充或更新当前 path 数据。

## 核心数据形态

高层上，请求负载大致是：

```json
{
  "model": {
    "name": "..."
  },
  "workflow_data": {
    "workflow_info": {},
    "protocols_info": {},
    "path_data": {
      "path_status": "waiting_for_research_goal",
      "steps": []
    }
  }
}
```

响应不是自由文本，而是如下几类结构化步骤之一：

- `AddResearchGoal`
- `AddResearchStrategy`
- `AddNextProtocol`
- `AddInitialValuesForFieldsInNextProtocol`
- `AddPhasedResearchConclusion`
- `AddFinalResearchConclusion`

## 为什么采用状态驱动

AIRA 不是每次都把整个科研流程重新塞进一个大 prompt 里再从头推导，而是显式推进工作流状态。

这种设计更利于：

- 检查中间步骤
- 重放或分叉 workflow
- 校验状态迁移
- 围绕当前阶段设计前端交互
- 对每一步单独做测试

实现代码位于 `packages/masterbrain/src/masterbrain/endpoints/aira/`。
