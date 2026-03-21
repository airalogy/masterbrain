# Changelog

## v0.7.0

### 新增功能

- `endpoints/chat/qa/language` 现在支持开启：1. 思考模式；2. 联网搜索
  端点输入结构如下：

  ```json
  {
      "model": {
          "name": "qwen3.5-flash", // 可以为qwen3.5-flash、qwen3.5-plus
          "enable_thinking": true, // 可以为true或false
          "enable_search": true // 可以为true或false
      },
      "messages": [
          {
              "role": "user",
              "content": "思考下你是谁？"
          }
      ]
  }
  ```

  返还为流式字符串。

  完整的流式返回字符串可如下：

  ```text
  <think>
  思考内容...
  </think>
  我是Airalogy Masterbrain。
  ```

  注意如果`enable_thinking`为`true`，则会返回思考过程，并使用`<think>`标签包裹。如果为`false`，则只返回最终结果，并不会有`<think>`标签。

  @荣璐 注意前端要能够自动渲染这个标签，以和正式文本相互区分。

### TODO

- `endpoints/chat/qa/vision`
- `endpoints/stt`

等端口还需要重构修改 @攀忠

## v0.6.0

- 完成AIRA功能及其API。

## v0.2.1

- `ChatDoc`中移除`chat_env`字段，以减少嵌套复杂度。详见：[`masterbrain.models.chat.ChatDoc`](/masterbrain/models/chat.py)。

## v0.2.0

- `chat`端口已经更新支持最新的`ChatDoc`作为数据模型的输入。详见：[`masterbrain.models.chat.ChatDoc`](/masterbrain/models/chat.py)。
- 更新支持最新`gpt-4o-mini`模型。

## v0.1.0

- `chat`端口支持通义千问模型：`qwen-long`。
  可以启动FastAPI后使用[chat_doc_qwen.jsonc](test/test_fastapi/test_router/test_chat/chat_doc_qwen.jsonc)在<http://127.0.0.1:8000/docs#/default/post_chat_api_chat_post>中进行测试（注意测试的时候删除jsonc中的注释，变为纯净的json格式）。
- 调整了调用tool时的`assistant`返回值，将`content`字段的`null`值改为`""`。这里的主要原因是，当为`null`时，OpenAI的模型能够正常运行，但Qwen的模型会报错。但改为`""`时，OpenAI和Qwen的模型都能够正常运行。因此，为了兼容性，将`null`改为`""`。（当然，这里Qwen报错的原因是Qwen的模型对`null`值的处理不够友好，这里只是为了兼容性考虑。）

    ```json
    {
        "role": "assistant", 
        "content": null, 
        "tool_calls": [
            ...
        ]
    }
    ```

    ```json
    {
        "role": "assistant", 
        "content": "", 
        "tool_calls": [
            ...
        ]
    }
    ```

- TODO: Qwen只支持Assistant-User交替的对话模式（其他商业模型也有类似的情况，比如文心一言），不支持Assistant-Assistant-User的对话模式。目前`scenario_messages`中的加入会导致出现Assistant-Assistant-User的对话模式。需要调整`scenario_messages`的注入逻辑还需要调整。
