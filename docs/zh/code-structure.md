# 代码结构

在`masterbrain`项目中，不同AI功能的代码管理主要是基于Endpoints。每个Endpoint对应一个特定的AI功能，负责处理相关的请求和响应，每个Endpoint具有独立的数据IO的类型约束和功能实现。其基本原则如下：

1. 每个Endpoint可以被视为一个相对独立AI功能的封装。因此，对于一个Endpoint而言，我们的首要封装目标是封装其数据IO的结构，也即，对于每个Endpoint，其输入和输出数据的结构必须要是稳定且可预期的。因此每个Endpoint需要具有一个独立的数据类型文件（`types.py`或文件结构复杂可用`types/__init__.py`）来对数据IO进行约束。也就是说，对于每个Endpoint，要能够让开发者只看`types.py`文件就能了解该Endpoint的输入和输出数据结构，而不需要深入到具体的实现细节中去（该设计有助于前后端容易协作）。
2. 由于在Masterbrain中，同一个Endpoint的功能可能采用多家不同AI供应商（如Qwen等）所提供的AI基座模型实现其功能。但是需要注意的是，Endpoint是针对功能的封装，为此，对于Endpoint的外部调用者来看，其不应该需要关心具体的模型实现细节，而只需要根据该Endpoint的数据IO约束对Endpoint进行调用即可。为此对于`types`而言，其应该针对每个Endpoint显式的声明所支持模型的名字。
3. 在Masterbrain中，Endpoint的实现是基于FastAPI的（在`masterbrain/fastapi`中定义了FastAPI的主应用程序`main.py`），因此每个Endpoint都需要有一个独立的FastAPI路由（`router`）来处理请求和响应。因此，在每个Endpoint的文件夹的根目录下，需要有一个`router.py`文件来定义FastAPI的路由。
4. 每个Endpoint的业务逻辑可以放到`<endpoint_name>/logic/`中进行组织。这样我们就可以尽量保持每个Endpoint根目录下的文件结构简单明了，避免过多的文件和复杂的目录结构。而如果外部用户要深入某个Endpoint的实现细节，则可以进入到`logic/`目录下查看具体的业务逻辑实现。

综上，`masterbrain`的代码结构大致如下：

```txt
masterbrain/
├── endpoints/
│   ├── <endpoint_name_1>/
│   │   ├── types.py
│   │   ├── router.py
│   │   ├── logic/
│   │   │   ├── <logic_file_1>.py
│   │   │   ├── <logic_file_2>.py
│   │   │   ├── ...
│   ├── <endpoint_name_2>/
│   │   ├── types.py
│   │   ├── router.py
│   │   ├── logic/
│   │   │   ├── <logic_file_1>.py
│   │   │   ├── <logic_file_2>.py
│   │   │   ├── ...
│   ├── ...
├── fastapi/
│   ├── main.py
...
```

如果有的Endpoint有2级或更多级的子Endpoint，则可以在其对应的文件夹下继续创建子文件夹来组织其子Endpoints。例如：

```txt
masterbrain/
├── endpoints/
│   ├── <endpoint_name_1>/
│   │   ├── <endpoint_name_1_sub_1>/
│   │   │   ├── types.py
│   │   │   ├── router.py
│   │   │   ├── logic/
│   │   ├── <endpoint_name_1_sub_2>/
│   │   │   ├── types.py
│   │   │   ├── router.py
│   │   │   ├── logic/
│   ├── <endpoint_name_2>/
│   │   ├── types.py
│   │   ├── router.py
│   │   ├── logic/
│   ├── ...
...
```

如果子Endpoint和上层级Endpoint共享相同的类型约束，则可以将其放在上层级Endpoint的`types.py`中进行定义，子Endpoint只需要引用上层级的类型即可，不要再重复定义。这样可以减少代码的冗余和维护成本。例如：

```txt
masterbrain/
├── endpoints/
│   ├── <endpoint_name_1>/
│   │   ├── types.py  # 包含上层级和子级
│   │   ├── <endpoint_name_1_sub_1>/
│   │   │   ├── router.py
│   │   │   ├── logic/
│   │   ├── <endpoint_name_1_sub_2>/
│   │   │   ├── router.py
│   │   │   ├── logic/
...
```

## Endpoints

每个有效的Endpoints都要在[endpoints/](endpoints/README.md)中进行说明，具体的Endpoints功能详见此文件。

## Types

由于在该代码架构下，不同的Endpoint独立指定可用的基座AI模型，因此每个Endpoint的`types.py`文件中需要显式声明所支持的模型名称。具体而言，通常我们在一个Endpoint的`types.py`文件中会有如下的结构：

```python
from typing import Literal
from pydantic import BaseModel

class EndpointInput(BaseModel):
    model: Literal["qwen3.5-flash"]
    # 定义其他输入字段
```

这里的`EndpointInput`类可以换位其他命名，如`AiraInput`, `ChatInput`等，以适应不同的Endpoint需求。**但是**，其必须包含一个`model`字段，用于指定所使用的AI模型名称。这个字段的类型是`Literal`，表示只能取特定的值，如`"qwen3.5-flash"`等。
