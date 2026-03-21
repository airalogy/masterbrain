# AI对话历史数据结构

## Messages

设计一个AI对话历史数据结构的核心在于设计其中Messages的数据结构。Messages是对话历史中，在AI-用户交互过程中产生的Message的列表。

在本项目中，Messages数据结构基于OpenAI的标准进行设计，兼容多模态对话历史、多轮对话历史、多工具对话历史等。

其设计理念是对话历史可以符合OpenAI的`chat.completions.create`函数的`messages`参数的传入要求，对话历史的每一轮对话都可以作为`messages`输入。由于OpenAI的`messages`的输入结构某种程度已经成为了LLM行业的标准，因此我们沿用。正因如此，该结构在稍加修改之后也适用于其他公司提供的LLM服务。

```py
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(completion.choices[0].message)
```

如果要了解OpenAI Chat相关API信息，请参考：

- [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat)

### Messages

在AI对话历史中，每一条Message都有一个`role`字段，用于标识这条消息是由用户、AI助手、工具等发出的。

下面是一个Messages的示例，其中包含了多种具有不同特性的Message：

```jsonc
[
    // 在真实对话中，第一条消息通常是系统消息。在此未示出


    // 简单对话

    // 术语：User Message
    {
        "role": "user",
        "content": "你是谁？"
    },
    // 术语：Assistant Message
    {
        "role": "assistant",
        "content": "我是Airalogy Masterbrain，一个由Airalogy和西湖大学开发的AI科学家助手。我专门为支持科学研究设计，旨在通过我的知识和能力加速科研效率和速度、提高科研质量、促进科研合作、推动科研创新。"
    },


    // 多模态对话

    // 术语：Multimodal Message
    {
        "role": "user",
        "content": [ // 当对话内容是多模态时，content是一个数组，每个元素是一个模态。用`type`字段来区分模态类型。
            {
                "type": "text",
                "text": "这张图片是什么？"
            },
            {
                "type": "image_url",
                "image_url": "https://www.westlake.edu.cn/images/header_white_icon.png"
            }
        ]
    },
    {
        "role": "assistant",
        "content": "这是西湖大学的标志。"
    },


    // 调用工具
    
    {
        "role": "user",
        "content": "请问PCR后，观察到的跑胶条带有杂带可能是什么原因？"
    },
    // 术语：Assistant Tool Call Message
    {
        "role": "assistant",
        "content": "", // 当有`tool_calls`字段时，`content`字段为空字符串，表示这是一个调用工具的消息
        "tool_calls": [ // tool_calls是一个数组。这意味着每次对话可以同时调用多个工具。但在实际应用中，通常只调用一个工具。
            {
                "id": "call_abc123", // 一个随机生成的ID，用于标识这次调用
                "type": "function",
                "function": {
                "name": "airalogy_search",
                "arguments": "{\"keywords\": [\"PCR\", \"跑胶条带\", \"杂带\"]}" // 这里arguments通常是一个JSON样字符串。里面的内容是根据具体的工具定义的。对于高级的工具，实际上也可以为空字符串。此时，工具端在应用工具时，可以将对话历史作为输入。
                    
                // 例如也可以如下
                // "arguments": "{\"search_by\": \"chat_history\"}" // 这意味着工具端需要使用对话历史作为输入，在搜索时工具除了把`arguments`传给工具外，还需要把对话历史传给工具。
                }
            }
        ]
    },
    // 术语：Tool Message
    {
        "role": "tool",
        "content": "{\"search_result\": \"可能是DNA污染或者PCR产物的二聚体\"}", // 工具返回的结果。注意这里总是把工具的返还封包为一个字符串。其经常是一个JSON字符串。
        "tool_call_id": "call_abc123" // 这个字段是为了标识这个结果是由哪次调用的工具返回的。当有多个工具调用时，会有多个"role": "tool"的消息，这个字段可以用来区分。
    },

    // 说明：上述这种tool的对话历史结构的设计十分巧妙，因为其实际上通过tool调用的方法，可以把tool执行的具体内部过程和对话历史解耦。在tool端，其为了生成tool的返还，可能需要多轮内部的对话，然而这些对话可以独立在tool端进行保存，而不用在主对话历史中体现。这样，主对话历史中只需要体现tool的返还结果即可。通过这种方法，时间实际上主对话历史和tool的内部对话历史是解耦的。如果我们要优化一个tool的性能，我们因而可以只关注tool的内部对话历史，并进行针对性的训练和优化

    // 注意，在前端对话显示时，通常会把Assistant Tool Call Message和Tool Message通过折叠的方式隐藏起来，用户想看到工具返回的结果时，可以点击展开。前端解析对话历史时，可以根据"role": "tool"的消息的"tool_call_id"字段来匹配对应的"role": "assistant"的消息，从而把工具返回的结果展示在对应的用户问题下面。
    {
        "role": "assistant",
        "content": "可能是DNA污染或者PCR产物的二聚体" // LLM基于工具返回的结果生成回答
    }
]
```

### UATA结构

在涉及工具调用的时候，其基本Messages：

1. User Message
2. Assistant Tool Call Message
3. Tool Message
4. Assistant Message

也就是说对于单一工具的调用，其通常只可能为如下2种形式：

- UATA (tool used): User Message -> Assistant Tool Call Message -> Tool Message -> Assistant Message
- UA (tool not used): User Message -> Assistant Message

### UAT1T2A结构

如果涉及到多个工具的调用，其基本Messages：

1. User Message
2. Assistant Tool Call Message
3. Tool Message 1
4. Tool Message 2
5. ...
6. Tool Message n
7. Assistant Message

在这种情况下，Assistant Tool Call Message中会有多个Tool Call，每个Tool Call对应一个Tool Message，LLM可以根据Tool Message的tool_call_id来理解哪个Tool Message是由哪个Tool Call产生的。

UAT1T2A结构常应用于多个工具调用的设计。

## `ChatDoc`

在真实AI Chat过程中AI Sever总是接收一个具有明确结构的JSON式的对话文档，并经由基于Pydantic的`ChatDoc`类进行解析。对话结束后，我们也总是返还一个处理后的`ChatDoc`。

下面为`ChatDoc`的示例数据结构：

```json
{
    "chat_id": "airalogy.id.chat.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "user_id": "zhangsan",
    "start_time": "2024-01-01T00:00:00+08:00",
    "end_time": "2024-01-01T00:01:00+08:00",
    "active": true,
    "deleted": false,
    "title": "询问你是谁",
    "model": {
        "name": "gpt-4o",
        "max_tokens": 512,
        "temperature": 0
    },
    "system_message_name": "masterbrain",
    "function_names": [],
    "context": {},
    "context_messages": [],
    "main_messages": [
        {
            "role": "user",
            "content": "你是谁？"
        },
        {
            "role": "assistant",
            "content": "我是Airalogy Masterbrain。"
        }
    ],
    "human_feedback": [
        {
            "score": 0,
            "additional": ""
        },
        {
            "score": 1,
            "additional": ""
        }
    ] 
}
```

各字段的具体说明如下：

- `chat_id`
  - Type: `str`
  - Description:
    - 对话的ID，通常基于UUID生成。
    - 注意，该ID可以作为外键在一个附表中记录对话的具体环境信息，例如对话是在什么界面上发生的，该界面所属的实验室、项目、RN等，这些信息可以用于鉴权。
  - Example: `"airalogy.id.chat.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`
- `user_id`
  - Type: `str`
  - Description:
    - 用户的ID。
    - 之所以要单独记录用户ID，是因为对话本质上都是私人的，都是由某个用户在Airalogy上发起的，因此无论对话是发生在哪个界面上，都一定包含用户ID。在显示对话历史时，我们可以根据用户ID来过滤对话历史，以保证用户的隐私。
  - Example: `"zhangsan"`
- `start_time` / `end_time`
  - Type: `datetime`
  - Description:
    - 对话开始/结束时间。
    - 用于前端在展示对话历史时，可以根据时间来排序，例如根据`end_time`可以将最新的对话排序最上面。
  - Example: `"2024-01-01T00:00:00+08:00"`
- `active`
  - Type: `bool`
  - Description:
    - 对于有的对话，由于其内容或长度等原因，可能不适宜于继续进行后续的对话。此时，我们可以将`active`字段设置为`false`，表示该对话已经被关闭。
  - Example: `True`
- `deleted`
  - Type: `bool`
  - Description:
    - 当用户在Airalogy上删除对话时，我们可以将`deleted`字段设置为`true`，表示该对话已经被删除。删除的对话不会在前端显示。
  - Example: `False`
- `title`
  - Type: `str`
  - Description:
    - 对话的标题。用于在前端展示对话历史时，可以根据标题来区分不同对话。
  - Example: `"询问你是谁"`
- `model`
  - Type: `dict`
  - Description:
    - 模型相关参数。
    - 用于记录对话使用的模型的参数。
  - `model.name`
    - Type: `str`
    - Description:
      - 模型的名称。
    - Example: `"gpt-4o"`
  - `model.max_tokens`
    - Type: `int`
    - Description:
      - 最大生成token数。
    - Example: `512`
  - `model.temperature`
    - Type: `float`
    - Description:
      - 温度参数。
    - Example: `0`
- `system_message_name`
  - Type: `str`
  - Description:
    - 系统消息的名称。
    - 用于调取系统消息的具体内容。
  - Example: `"masterbrain"`
- `function_names`
  - Type: `list[str]`
  - Description:
    - AI可以调用的工具的名称。
    - 当不调用工具时，可以为空列表。
  - Example: `[]`
- `context`
- `main_messages`
  - 详见下文
- `human_feedback`
  - Type: `list[HumanFeedback]`
  - Description:
    - 用户对每一条消息的反馈。用于记录用户对每一条消息的反馈，例如赞、踩等。列表长度等于`main_messages`的长度，用于记录用户对每一条消息的反馈。
  - `HumanFeedback.score`
    - Type: `int`
    - Description:
      - 用户的反馈。0: 无反馈；1: 赞；-1: 踩。
    - Example: `0`
  - `HumanFeedback.additional`
    - Type: `str`
    - Description:
      - 用户的额外反馈。
    - Example: `""`

### `context_messages` / `main_messages`

在`masterbrain`中，为了构造完整的对话历史，我们实际上是根据`system_message_name`来调取系统消息的内容，然后我们将基于此构造的`system_message` + `context_messages` + `main_messages`作为完整的对话历史。这个完整的对话历史可以用于传入模型。

在某些情况下，`context_messages`可以用于作为Few-shot Message的嵌入位置。

对于`context_messages`和`main_messages`，为了保证对话的安全性，其可用的`role`字段只有`user`, `assistant`或`tool`。`system`出于对话安全的考虑是不允许的。

### `context`

`context`的主要功能是用于提示Chat前端哪些Context已经被注入到了Chat的对话历史中，以方便前端能够进行正确的显示和控件展示（例如展示哪些历史Records已经被注入到了Chat中）。

该设计的一个优势是，如果没有该字段，前端为了能够了解Chat中已经注入的Context，其需要解析整个对话历史，这样会增加前端的负担。而有了该字段，前端只需要解析该字段即可。
