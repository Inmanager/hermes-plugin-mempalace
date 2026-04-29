# Hermes Agent MemPalace 记忆插件
[English](README.md) | 中文版

## 这是什么？
这是一个为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 编写的**长时记忆插件**。它让 Hermes 拥有了“长期记忆”，这样它就能记住你们在不同天数、不同会话中聊过的内容。

## 它和 MemPalace 是什么关系？
[MemPalace](https://github.com/MemPalace/mempalace) 是一个非常优秀的、完全本地化的 AI 记忆数据库。你可以把它想象成 AI 的一个井井有条的大脑或文件柜。

这个插件则是连接 Hermes Agent 和 MemPalace 的**桥梁**。
- MemPalace 负责所有的重活：存储事实、生成文本向量、搜索上下文。
- 这个插件负责告诉 Hermes *如何*与 MemPalace 沟通，让 Hermes 能够自动保存你的对话，并在回复你之前自动回想起过去的事实。

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
