# Hermes Agent MemPalace 记忆插件
[English](README.md) | 中文版

## 这是什么？
这是一个为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 编写的**长时记忆插件**。它让 Hermes 拥有了“长期记忆”，这样它就能记住你们在不同天数、不同会话中聊过的内容。

## 它和 MemPalace 是什么关系？
[MemPalace](https://github.com/MemPalace/mempalace) 是一个非常优秀的、完全本地化的 AI 记忆数据库。你可以把它想象成 AI 的一个井井有条的大脑或文件柜。

客观地说，MemPalace 本身提供了标准的 MCP (Model Context Protocol) 接口，这意味着在支持 MCP 的客户端中，它是完全可以“开箱即用”的。

**既然可以开箱即用，为什么还要专门开发这个插件？**

虽然通过 MCP 协议调用 MemPalace 是可行的，但这存在一个架构层面的痛点：**高昂的 Token 消耗与额外的请求延迟**。在传统的 MCP 模式下，记忆的存储与检索都被封装为提供给大模型的“工具（Tools）”，系统需要将冗长的工具定义说明、调用过程以及检索结果作为对话上下文反复传递给 LLM。对于高频触发的记忆管理操作而言，这不仅浪费了宝贵的 Token 额度，还会拖慢大模型的响应速度。

为了解决这一问题，本插件采用了更优化的接入方式：
- **原生管线集成（Native Pipeline Integration）**：插件绕过了通用的 MCP 协议层，通过内部 API 将 MemPalace 的核心能力直接、无缝地接入到 Hermes Agent 的底层记忆处理管线中。
- **静默上下文注入（Silent Context Injection）**：MemPalace 依然负责文本向量化和相似度搜索等高负载运算，而本插件会在大模型生成回复前，在后台默默将相关的记忆预加载进系统上下文，并在对话后自动异步归档。
- **极致的性能与成本优化**：无需让 LLM 频繁“主动调用工具”来回忆过去。在赋予 Hermes 长期记忆能力的同时，实现了零额外交互轮次，将 Token 开销和延迟降到了最低。

## 我为什么需要它？（能干嘛）
默认情况下，当你和 Hermes 开始一个新对话时，它会忘记之前所有的聊天内容。
启用这个插件后：
- **记住你是谁**：告诉 Hermes 一次你的名字或偏好，它永远都不会忘。
- **跨会话回忆**：如果你问“我们昨天在做什么项目？”，Hermes 可以搜索它在 MemPalace 中的大脑并直接告诉你。
- **后台自动同步**：你不需要做任何额外操作。每次 Hermes 回复你时，它都会悄悄地将你们的对话存档到 MemPalace 中。
- **上下文预加载**：在 Hermes 思考如何回复你之前，这个插件会偷偷在过去的记忆中搜索相关的上下文，并把它们作为背景资料塞给 Hermes。
- **100% 本地且免费**：它完全在你的电脑上运行。没有 API 调用费，没有订阅，也不会将你的隐私数据发送到云端。

## 小白安装教程

### 第一步：安装引擎（MemPalace）
首先，我们需要把 MemPalace 引擎安装到 Hermes 的 Python 环境中。
打开终端，运行：
```bash
~/.hermes/hermes-agent/venv/bin/pip install mempalace chromadb orjson
```

### 第二步：下载插件
将这个插件下载到 Hermes 的插件目录中：
```bash
git clone https://github.com/Inmanager/hermes-plugin-mempalace ~/.hermes/plugins/mempalace
```

### 第三步：启用插件
告诉 Hermes 以后使用这个新的记忆插件。
首先，在终端启用插件：
```bash
hermes plugins enable mempalace
```

然后，编辑你的 Hermes 配置文件 (`~/.hermes/config.yaml`)，将其设置为默认的记忆提供者。找到或添加 `memory` 这一段：
```yaml
memory:
  provider: mempalace
```

### 第四步：检查是否成功
运行以下命令来检查是否生效：
```bash
hermes memory status
```
如果你看到活动提供者（active provider）显示为 `mempalace`，那么一切就绪啦！

## 如何更新（老用户升级）
如果你之前已经安装过旧版本，现在想要更新到最新版（比如 v1.1.0，包含重要错误修复），只需要打开终端，运行下面这一行命令：
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```
更新完成后，重启你的 Hermes 即可生效！完全不需要重新配置。
