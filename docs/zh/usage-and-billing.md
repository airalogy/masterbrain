# 模型用量与计费集成

Masterbrain 会把 LiteLLM 和少量 provider-specific runtime 的返回值统一成
稳定的用量契约。Platform 等宿主应用只需持久化不可变事件，再使用自己的
版本化价目表完成计费，不需要为每个模型 SDK 分别实现统计逻辑。

## 职责边界

- LiteLLM 或供应商 SDK 提供原始 token 数量，以及可用时的供应商成本估算。
- Masterbrain 负责字段归一化、请求关联、逐调用事件、聚合和 `UsageSink` 投递。
- Platform 负责租户和用户身份、价格版本、额度、账单、币种、税费、退款与对账。

不要直接用 `provider_cost` 计算用户账单。这个字段会同时保存明确的
`provider_cost_currency` 和 `provider_cost_source`，适合分析上游成本和辅助对账，
但供应商价格映射和汇率都可能变化。正式账单应同时保存原始 usage 事件、
命中的价格规则以及 Platform 计费币种下当时的价格快照。

## 稳定的数据结构

每次真实的上游模型调用都会产生一个 `ModelUsageEvent`，其中的 `usage` 类似：

```python
ModelUsage(
    provider="qwen",
    requested_model="qwen3.5-flash",
    resolved_model="qwen3.5-flash-2026-07-01",
    input_tokens=1200,
    output_tokens=300,
    cached_input_tokens=800,
    cache_creation_input_tokens=0,
    reasoning_tokens=100,
    total_tokens=1500,
    provider_cost=Decimal("0.018"),
    provider_cost_currency="CNY",
    provider_cost_source="provider",
    source="provider",
)
```

事件还包含幂等键 `event_id`、调用 ID、供应商请求 ID、状态、耗时、时间戳、
调用类型和业务上下文。即使上游失败或被取消、无法取得 token 数，也会产生
相应状态的事件，便于排查和对账。

## Platform 持久化

在服务启动时注册服务端 sink，并对 `event_id` 建立唯一约束：

```python
from masterbrain.usage import ModelUsageEvent, configure_usage_sinks


class PlatformUsageSink:
    def __init__(self, usage_repository):
        self.usage_repository = usage_repository

    async def record_usage(self, event: ModelUsageEvent) -> None:
        await self.usage_repository.insert_if_absent(
            event_id=event.event_id,
            payload=event.to_dict(),
        )


configure_usage_sinks(PlatformUsageSink(usage_repository))
```

sink 异常会被记录，但不会把已经成功的模型响应改成用户请求失败。因此生产
计费 sink 应使用可靠持久化，监控写入失败，并保留与供应商报表进行补偿对账的
能力。

## 可信业务身份

内置 FastAPI middleware 会为请求绑定 operation，并在响应头返回
`X-Masterbrain-Operation-Id`。绑定会覆盖完整的流式响应生命周期。

默认实现只接受请求关联信息，不会相信客户端随意传入的租户或用户 header。
Platform 应从服务端认证结果构造上下文：

```python
from masterbrain.fastapi.usage import install_usage_context_middleware
from masterbrain.usage import UsageContext


def platform_usage_context(request):
    principal = request.state.principal
    return UsageContext(
        operation_id=request.headers.get("X-Masterbrain-Operation-Id")
        or create_operation_id(),
        request_id=request.headers.get("X-Request-Id"),
        feature=f"{request.method} {request.url.path}",
        tenant_id=principal.lab_id,
        user_id=principal.user_id,
        project_id=request.path_params.get("project_id"),
    )


install_usage_context_middleware(app, context_factory=platform_usage_context)
```

如果 Platform 直接调用 Masterbrain 函数而不是使用它的 ASGI middleware，
可以在一次业务操作外层使用 `bind_usage_context(UsageContext(...))`。

## 定价与聚合

`aggregate_usage_events(events, operation_id=...)` 可生成一次操作的汇总数据，
其中成本按币种分组，不会隐式换汇。正式计费仍应逐事件计算，因为同一次操作
可能包含不同供应商、模型、缓存费率或调用类型。如果同一 operation 中的租户、用户、
项目或对话身份冲突，聚合会直接拒绝。建议价目表匹配键为：

```text
(provider, resolved_model, call_type, price_version, started_at)
```

`requested_model` 表示用户或产品选择，`resolved_model` 表示供应商实际执行的
模型版本。两者同时保存，才能兼顾产品语义、模型差异和历史对账。

## 已覆盖的调用路径

Masterbrain 当前统一捕获：

- LiteLLM 普通和流式 chat completion
- LiteLLM 音频转录
- 论文生成使用的 LangChain 调用
- 直接调用 DashScope 的语音转文字
- OpenCode 代码编辑过程中每一次 assistant/provider 调用

流式 LiteLLM 请求会自动开启 `stream_options.include_usage`。LiteLLM
价格表计算的成本会标记为 `USD`；供应商原生成本则必须保存其返回的币种，
例如人民币账单使用 `CNY`。Masterbrain 不做汇率转换。调用方需要把流
消费完，或显式调用 `aclose()`，才能记录最终用量或取消事件。
