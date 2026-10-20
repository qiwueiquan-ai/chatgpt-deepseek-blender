# ChatGPT × DeepSeek × Blender

**通过 GitHub Issues / Actions 协调 ChatGPT、DeepSeek API 与 Blender 的开源自动建模原型。**

> **状态：v0.1.0（开源预览）**。核心“指令下达 → DeepSeek 回答 → Blender 运行范例 → 上传可编辑 .blend 和预览 PNG”链路已在私有原型中验证。本仓库提供可自行部署的代码，不是即装即用的 Blender 插件，也未实现自主视觉验收闭环。

## ✨ 能做什么

- **指令中继**：在 GitHub Issue 中发出设计/编程任务，GitHub Actions 调用 DeepSeek 官方 API，将文本/脚本回复写回 Issue。
- **ChatGPT 指挥**：如果你的 ChatGPT 账户连接了 GitHub，且允许操作该仓库，可以由 ChatGPT 发布任务、审查回复、提出新一轮修改要求。
- **示例自动建模**：提供一份已实测可运行的 Blender 4.x 现代小房子 Python (`bpy`) 示例，并通过 GitHub Actions 在 Linux 上无界面执行、渲染。
- **取回成品**：示例工作流上传 `house_v1.blend` 与 `house_v1_preview.png` 作为 GitHub Actions Artifact，可下载继续编辑。

## 工作原理

```text
用户 ─→ ChatGPT（需求解释 / 任务拆分 / 人工审核）
               │ (GitHub connector，需授权)
               ▼
           GitHub Issue
               │ (Actions)
               ▼
           DeepSeek API
               │ (代码/文本回复)
               ▼
         GitHub Issue 评论 ─→ ChatGPT 读取 / 审查
                                     │
                             提交经过审核的 bpy 脚本
                                     ▼
                          GitHub Actions + Blender
                                     ▼
                      .blend 模型 + PNG 渲染 Artifact
```

**安全边界：** 模型回复只是文本，**不会**直接作为任意 Python 脚本自动执行。Blender 演示工作流只运行仓库内经过检查并提交的 `scenes/house_v1.py`。需要更复杂的“回复自动运行”功能时，必须先加入沙箱、命令限制及代码审核机制。

## 🚀 五分钟开始

1. **Fork 本仓库** 到你自己的 GitHub 账户（或复制源码到自己的仓库）。若仓库是公开的，请注意 **Issue 内容和模型回复也是公开的**，不要提交私人设计或商业敏感资料。
2. 准备自己的 [DeepSeek 官方 API Key](https://platform.deepseek.com/)。
3. 打开你的仓库 → **Settings → Secrets and variables → Actions → New repository secret**。名称为 `DEEPSEEK_API_KEY`，内容为你的密钥。**不要把密钥放入仓库文件或 Issue**。
4. 打开 **Actions**，按 GitHub 提示启用工作流。若 Fork 默认禁用了 Actions，需要先启用。
5. 打开 **Issues → New issue**，标题必须以 `[DeepSeek]` 开头，例如 `[DeepSeek] 连接测试`；正文写 `请回复 CONNECTED`。GitHub Actions 成功后，`github-actions[bot]` 会在 Issue 下留言。
6. 在同一个 Issue 下继续评论，即可进行多轮文字或代码交流。为避免滥用，只有**由仓库所有者创建**且标题符合规则的 Issue，以及**仓库所有者发出的评论**才触发 DeepSeek 调用。

如果你只想测试建模而不设置 DeepSeek：进入 **Actions → Render House v1 → Run workflow**，等待成功运行后，打开对应运行记录，在 **Artifacts** 下载包含 `.blend` 和预览图的压缩包。

**详细步骤见：** [中文零基础部署教程](docs/quickstart-zh.md)。

## 📁 文件结构

```text
.github/workflows/
  deepseek-relay.yml     # owner-only Issue/评论触发，调用 DeepSeek
  render-house.yml       # Ubuntu 安装 Blender，运行小房子范例并上传产物
scripts/
  relay.py               # 标准库 Python DeepSeek / GitHub API 中继
scenes/
  house_v1.py            # Blender 建模与渲染示范
docs/
  quickstart-zh.md       # 中文图文式菜单操作说明
  architecture.md        # 架构、能力边界、开发路线图
LICENSE                  # MIT
SECURITY.md              # 安全注意事项
.gitignore
```

## 🧪 已完成与未完成

| 功能 | 状态 |
| --- | --- |
| ChatGPT 通过已连接的 GitHub 发布任务 | ✅ 私有原型已验证 |
| DeepSeek API 接收任务、回传代码 | ✅ 私有原型已验证 |
| Blender 后台执行示例 `bpy` | ✅ Blender 4.0.2 已验证 |
| 输出可编辑 `.blend` + 预览 PNG | ✅ 已验证 |
| 每次 DeepSeek 回复自动执行并渲染 | ❌ 尚未实现（故意保留安全审核） |
| ChatGPT 自动观看渲染并评价/纠错 | ⚠️ 需要能够访问并读取渲染图的运行环境，尚未闭环 |
| 本地 Windows Blender 自动同步 | ❌ 尚未实现 |
| 适用于任意复杂场景的稳定成品质量 | ❌ 尚未验证 |

## 🔐 安全与费用

- DeepSeek Key 通过 GitHub Actions Secret 注入；Fork **不会复制**原仓库 Secret。
- 使用者自己承担 DeepSeek API 消耗，GitHub Actions 也可能消耗账户计算分钟与 Artifact 存储额度。
- 公开仓库中的 Issue、源码、PR 及 Artifact 可能被其他人访问；私密设计请使用**自己的私有 Fork/仓库**。
- 不要不经审查运行 AI 生成的任意 Python 程序；`bpy` 脚本具有文件和网络访问能力。
- 免费或收费套餐、各项限额及 GitHub Actions 可用性以对应服务提供商当前政策为准。

## 许可证与贡献

源码以 [MIT License](LICENSE) 许可。欢迎通过 Issue 提交复现步骤或 Pull Request 改进工程质量和易用性。发布前请勿包含 API Key、个人信息及未经许可的受版权保护资源。

> 本项目为独立的社区原型，不隶属于 OpenAI、DeepSeek 或 Blender Foundation。“ChatGPT”与“DeepSeek”为各自权利人的商标。

---
**English quick note:** An experimental, self-hosted GitHub Issues → DeepSeek API relay, plus a reviewed Blender Python house example rendered by GitHub Actions. Bring your own DeepSeek API key. Model-generated code is **not** auto-executed. See the Chinese setup guide for installation.

## ps
自己搞着玩的
