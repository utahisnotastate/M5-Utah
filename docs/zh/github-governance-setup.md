# GitHub 治理配置

## `main` 分支保护

请启用：

- 合并前必须通过 PR
- 至少 1 个审批
- 新提交后清除旧审批
- 必须通过状态检查：
  - `quality`
  - `analyze`
- 必须解决所有对话

启用后即可移除 GitHub 上 “your main branch isn't protected” 的提示横幅。

### 可选自动化（GitHub CLI）

如果已安装并登录 `gh`：

```powershell
./scripts/enable_branch_protection.ps1
```

## 安全设置

- 开启 Dependabot alerts
- 开启 code scanning alerts
- 如可用，开启 secret scanning
