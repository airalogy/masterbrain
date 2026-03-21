# Endpoints of Airalogy Masterbrain

在Airalogy Masterbrain中，由于涉及众多的AI功能，为了方便管理，我们进行以下设计：

每个需要区别的功能可以通过一个Endpoint来区分，具有关联性的功能可以通过嵌套的方式来组织。我们将其放置于`/endpoints/`下。例如，我们常用以下的endpoints：

- `/endpoints/chat`：凡是交互方式是类似普通对话的，都可以放入此endpoint下。其进一步包含以下子Endpoints：
  - `/endpoints/chat/qa`: 用于QA模式问答的对话端点。支持Protocols, Records, Discussions嵌入。
    - `/endpoints/chat/qa/language`: 用于语言模型的对话端点（支持文本输入）。
    - `/endpoints/chat/qa/vision`: 用于视觉模型的对话端点（支持图像输入）。
  - `/endpoints/chat/field_input`: Airalogy Record Field Input的对话采用此endpoint。
  - `/endpoints/chat/hub`：Airalogy Hub中所采用的对话端点。
- `/endpoints/protocol_generation`：Protocol Generation相关的端点。其进一步包含此下的子Endpoints：
  - `/endpoints/protocol_generation/aimd`: 用于生成Airalogy Markdown的端点。
  - `/endpoints/protocol_generation/model`: 用于Airalogy Protocol Model生成的端点。
  - `/endpoints/protocol_generation/assigner`: 用于生成Airalogy Protocol Assigner的端点。
- `/endpoints/protocol_check`：用于检查一个Airalogy Protocol语法的端点。
- `/endpoints/protocol_debug`: 用于Protocol Debug的端点。
- `/endpoints/aira`: 和AIRA方法相关的实现采用此endpoint。
