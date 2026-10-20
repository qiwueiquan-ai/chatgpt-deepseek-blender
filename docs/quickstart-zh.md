# 零基础部署指南（中文）

## 一、复制项目

打开项目主页，点击右上角的 **Fork**，将它复制到你自己的 GitHub 账户。

**注意：** 如果你希望设计任务不被其他人看到，请使用你自己的私有仓库，不要在公开 Issue 中放私人内容。

## 二、配置 DeepSeek API Key

1. 打开 [DeepSeek 开放平台](https://platform.deepseek.com/)，自行创建 API Key。
2. 回到自己的 GitHub 仓库，点击顶部 **Settings（设置）**。
3. 左侧找到 **Secrets and variables（密钥与变量）** → **Actions**。
4. 点击 **New repository secret（新建仓库密钥）**。
5. **Name** 填 `DEEPSEEK_API_KEY`，**Secret** 粘贴你的密钥，点击 **Add secret**。
6. 密钥保存后 GitHub 不会再次显示密钥全文，这是正常现象。

> 不要通过聊天、Issue 或代码分享密钥。原仓库的密钥不会随着 Fork 自动过来。

## 三、启用自动化

打开 **Actions** 页面。如果看到允许启用工作流的提示，按提示启用。建议先阅读 `.github/workflows/deepseek-relay.yml` 的内容再启用。

## 四、第一次测试（文字链路）

1. 打开仓库顶部的 **Issues**。
2. 点击 **New issue**，标题输入 `[DeepSeek] 连接测试`，正文输入 `请只回复 CONNECTED`。
3. 点击 **Submit new issue**。
4. 进入 **Actions**，查看名为 **DeepSeek Relay** 的任务是否成功。
5. 稍等后回到 Issue，应该会看到来自 `github-actions[bot]` 的回复。
6. 后续在**同一 Issue** 下评论，可以继续生成文本或 Blender Python 代码。

如果没有回复：先检查 Actions 是否启用、Issue 标题是否以 `[DeepSeek]` 开头、是否由仓库所有者创建、`DEEPSEEK_API_KEY` 是否已配置、账户余额/额度是否充足，以及 Actions 的错误日志。

## 五、第一次生成 Blender 文件（无需 DeepSeek）

1. 打开 **Actions → Render House v1**。
2. 选择 **Run workflow**（需要确保已启用 Actions）。
3. 等运行结果变绿，再点击这次运行记录。
4. 在 **Artifacts** 找到 `house-v1-model-preview` 并下载。
5. 解压后可得到：
   - `house_v1.blend`：Blender 可编辑模型
   - `house_v1_preview.png`：渲染预览图

这只是运行仓库内现成的、经过测试的建模脚本，并**不是**自动执行 Issue 中生成的任意代码。

## 六、如何配合 ChatGPT

若你的 ChatGPT 账户已连接 GitHub，而且 ChatGPT 可以访问并对你的 Fork 创建 Issue / 评论，则你可以让 ChatGPT：

- 整理建模需求，发布标题为 `[DeepSeek] ...` 的任务；
- 稍后读取机器人回复的代码；
- 对结果进行代码审查、要求 DeepSeek 修改；
- 在审核后将代码作为仓库文件提交，供经授权的 Blender 工作流使用。

不同 ChatGPT 账户、插件授权和工作模式下的可用操作可能不同。若无法直接写仓库，也可以手动创建 Issue/提交代码，仍能使用 GitHub 工作流。

## 七、常见问题

- **为什么创建了 Issue 却没运行？** 检查用户身份、标题前缀和 Actions 启用状态。
- **为什么 Blender 工作流要等一会儿？** GitHub 需要分配临时机器、安装 Blender 并渲染。
- **生成文件在哪里？** 在对应工作流运行记录的 Artifacts 中，不会自动下载到你电脑。
- **为什么没有自动执行 DeepSeek 输出的脚本？** 为防止执行恶意/错误代码，模型输出与实际代码运行是两个独立阶段。
- **需要 OpenAI API Key 吗？** 本项目的 GitHub → DeepSeek API 中继**不需要**，但是否能直接从 ChatGPT 操作 GitHub 取决于其连接与授权能力。
