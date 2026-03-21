<div align="center">

# Masterbrain API

<p align="center">
  <a href="#安装与设置">安装与设置</a> •
  <a href="#功能模块">功能模块</a> •
  <a href="#API文档">API文档</a>
</p>

</div>

## 安装与设置

所有Airalogy Masterbrain相关API使用FastAPI进行本地部署。使用时需要先启动FastAPI服务，然后调用API。

### 1. 安装`Miniconda`或`Anaconda`

### 2. 创建`conda`环境

```shell
conda create -n masterbrain python=3.12
conda activate masterbrain
```

### 3. 安装`masterbrain`包

```shell
# 生产环境
pip install .

# 开发环境（editable mode/develop mode）
pip install -e .

# 安装dev依赖（包含pytest等）
pip install ".[dev]"
# 或者
pip install -e ".[dev]"
```

### 4. 设置环境变量

将`.env.example`文件拷贝为`.env`，并根据说明进行配置。

```shell
cp .env.example .env
```

### 5. 启动FastAPI服务

```shell
# 生产环境
uvicorn masterbrain.fastapi.main:app --host 127.0.0.1 --port 8080

# 开发环境
uvicorn masterbrain.fastapi.main:app --reload --host 127.0.0.1 --port 8080
```

端口可以根据实际情况进行修改。

## 功能模块

Masterbrain API提供以下主要功能模块：

### 聊天功能 (Chat)

- **标准聊天**: `/api/chat/chat` - 提供基础聊天功能
- **视觉功能**: `/api/chat/vision` - 支持图像处理和分析
- **语音转文字**: `/api/chat/stt` - 支持语音输入转换为文字
- **Hub聊天**: `/api/chat/hub_chat` - 集成化聊天功能
- **字段输入**: `/api/chat/field_input` - 结构化字段输入处理

### 协议生成 (Protocol Generation)

- **AIMD协议**: `/api/tool/protocol_aimd` - AI模型驱动协议生成
- **模型协议**: `/api/tool/protocol_model` - 模型相关协议生成
- **分配器协议**: `/api/tool/protocol_assigner` - 任务分配协议生成

### 协议检查与调试 (Protocol Check & Debug)

- **协议检查**: `/api/tool/protocol_check_round` - 验证协议有效性
- **协议调试**: `/api/tool/protocol_debug` - 协议调试工具

### AIRA工作流 (AIRA Workflow)

- **OpenAI集成**: `/api/tool/workflow` - 集成工作流

## API文档

服务启动后，可以访问以下地址查看API文档：

- 默认地址: `http://127.0.0.1:8080/docs`
- 如果修改了Host和Port，请根据实际情况访问对应地址

<p align="center">
  <img src="docs/images/preview.png" width="80%" alt="API预览界面">
</p>

## 引用

如果您在研究或项目中使用了Airalogy Masterbrain，请引用以下文献：

```bibtex
@misc{yang2025airalogyaiempowereduniversaldata,
      title={Airalogy: AI-empowered universal data digitization for research automation}, 
      author={Zijie Yang and Qiji Zhou and Fang Guo and Sijie Zhang and Yexun Xi and Jinglei Nie and Yudian Zhu and Liping Huang and Chou Wu and Yonghe Xia and Xiaoyu Ma and Yingming Pu and Panzhong Lu and Junshu Pan and Mingtao Chen and Tiannan Guo and Yanmei Dou and Hongyu Chen and Anping Zeng and Jiaxing Huang and Tian Xu and Yue Zhang},
      year={2025},
      eprint={2506.18586},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.18586}, 
}
```
