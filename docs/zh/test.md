# Test for `masterbrain`

测试相关代码都储存在`/test`目录下。

使用`pytest`进行测试。

测试中分为2种类型：

1. 可以直接运行的测试
2. 需要调用API的测试（例如需要调用`openai`API相关的测试）。此类型的测试往往：1. 依赖于网络环境；2. 运行需要应用第三方API，因而需要支付费用；因此，不适合在每次测试时都运行。

对于后者，此类型的测试在编写的时候需要打上标签，如`@pytest.mark.openai_api`。

例如：

```python
import pytest

@pytest.mark.openai_api
def test_openai_api():
    pass
```

默认情况下，由于`pytest.ini`中设置了：

```ini
addopts = "not openai_api qwen_api"
```

以下命令不会运行如下类型的测试：

- `openai_api`,
- `qwen_api`

```shell
pytest
```

如果想要运行上述类型的测试，可以使用`-m`参数。

```shell
pytest -m "openai_api"

# or
pytest -m "qwen_api"
```

**！！！注意！！！：运行`openai_api`类型的测试时，请确保OpenAI服务可用并符合使用和法律规范。**
