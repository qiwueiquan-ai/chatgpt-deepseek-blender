# 安全须知 / Security

这是一个实验性跨服务自动化原型，**不是安全沙箱**。

## 凭据

- 在 GitHub 仓库 Settings → Secrets and variables → Actions 中单独设置 `DEEPSEEK_API_KEY`。
- 不要把 API Key 放在 Issue、评论、PR、仓库源代码、公共日志或 Blender 文件里。
- Fork/复制仓库时，**原仓库的 Secrets 不会随之复制**。
- 如果密钥意外泄露：立即到 DeepSeek 控制台撤销，生成新密钥后重新配置。

## 发布内容的可见性

- 公开仓库的 Issues、评论、提交以及公开运行产生的 Artifacts 可能被其他人访问。
- 用户不应该在公开 Issue 中输入隐私、机密设计、内部程序或个人信息。需要保密，请使用私有仓库。
- 即使 Issue 已删除，内容可能曾被第三方获取；不要依赖删除来保证保密。

## 自动执行风险

- DeepSeek 的输出作为**不可信文本**处理。
- `scripts/relay.py` 只将模型回复写到 Issue 评论区，不自动作为代码运行。
- `render-house.yml` 仅执行仓库维护者明确提交的示范 `scenes/house_v1.py`。
- Blender 的 `bpy` 脚本本质上是 Python，可以读写文件、联网和执行系统命令。维护者应审查每个变更，并采取最小权限、隔离运行和执行时限等措施。
- 不要把完整 GitHub Token 或 DeepSeek 密钥传入未经审查的 Blender Python 脚本。

## 自动化授权与费用

- Issue 触发条件限制为仓库所有者所创建的 `[DeepSeek]` Issue，且后续仅允许所有者评论触发 API。
- GitHub Actions 的内置 Token 仅授予必要的 `contents: read` / `issues: write` 权限。
- 维护者需要自行管理 DeepSeek 消费限额与 GitHub Actions 配额。
- 如发现漏洞，不要在公开 Issue 中发送漏洞利用时涉及的私人密钥；请通过 GitHub 提供的私人渠道联系维护者。
