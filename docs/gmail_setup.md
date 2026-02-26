# Gmail IMAP 设置指南

Job Hunter 现在支持直接从 Gmail 读取面试相关邮件，方便快速查看面试邀请、安排时间等。

## 功能

- **读取邮件**: 按主题搜索并读取特定邮件内容
- **搜索邮件**: 列出匹配的邮件列表
- **面试安排**: 结合面试调度器，基于邮件内容推荐最佳时间段

## 前置要求

1. Gmail 账号（推荐你的主邮箱）
2. 开启 Gmail 两步验证（2-Step Verification）
3. 生成应用专用密码（App Password）

---

## 设置步骤

### 步骤 1: 开启 Gmail IMAP 访问

1. 打开 Gmail，点击右上角的 **设置图标**（齿轮图标）
2. 选择 **"查看所有设置"**（See all settings）
3. 点击 **"转发和 POP/IMAP"**（Forwarding and POP/IMAP）标签
4. 在 **"IMAP 访问"**（IMAP access）部分，选择 **"启用 IMAP"**（Enable IMAP）
5. 点击底部的 **"保存更改"**（Save Changes）

### 步骤 2: 开启两步验证

应用专用密码需要开启两步验证后才能使用。

1. 访问 [Google 账号安全设置](https://myaccount.google.com/security)
2. 在 **"登录 Google"**（Signing in to Google）部分，找到 **"两步验证"**（2-Step Verification）
3. 点击并按照提示开启两步验证
   - 可以使用手机作为第二验证因素
   - 也可以使用 Google Authenticator 应用

> ⚠️ **注意**: 开启两步验证后，你的 Google 密码将无法直接用于第三方应用登录，需要使用应用专用密码。

### 步骤 3: 生成应用专用密码

1. 访问 [Google 账号安全设置](https://myaccount.google.com/security)
2. 在 **"登录 Google"**（Signing in to Google）部分，点击 **"应用专用密码"**（App passwords）
   - 如果看不到此选项，说明两步验证尚未开启
3. 在 **"选择应用"**（Select app）下拉菜单中，选择 **"邮件"**（Mail）
4. 在 **"选择设备"**（Select device）下拉菜单中，选择 **"其他（自定义名称）"**（Other）
5. 输入一个名称，例如: `Job Hunter`
6. 点击 **"生成"**（Generate）
7. **复制生成的 16 位密码**（格式如: `xxxx xxxx xxxx xxxx`）
   - ⚠️ **重要**: 这个密码只会显示一次，请务必保存好！

### 步骤 4: 配置环境变量

编辑项目根目录下的 `.env` 文件，添加：

```env
# --- Gmail IMAP (for reading interview emails) ---
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

## 使用方法

### 测试连接

```bash
python scripts/job_pipeline.py --test-gmail
```

### 读取特定邮件

例如，读取 FareHarbor 的面试安排邮件：

```bash
python scripts/job_pipeline.py --read-email "FareHarbor"
```

或者更精确的主题：

```bash
python scripts/job_pipeline.py --read-email "Interview Availability"
```

指定搜索更长时间范围（默认7天）：

```bash
python scripts/job_pipeline.py --read-email "FareHarbor" --lookback-days 14
```

### 搜索邮件列表

```bash
python scripts/job_pipeline.py --search-emails "interview"
```

### 完整面试安排流程

1. **读取面试邮件**:
   ```bash
   python scripts/job_pipeline.py --read-email "FareHarbor"
   ```

2. **查看可用时间段**:
   ```bash
   python scripts/job_pipeline.py --suggest-availability "FareHarbor" --duration 30
   ```

3. **获取推荐时间段**:
   ```bash
   python scripts/job_pipeline.py --schedule-interview "FareHarbor" --duration 30
   ```

---

## 常见问题

### Q: 提示 "Authentication failed"

- 检查 `GMAIL_EMAIL` 是否正确
- 检查 `GMAIL_APP_PASSWORD` 是否正确（注意空格）
- 确保已开启两步验证
- 确保已开启 Gmail IMAP 访问

### Q: 提示 "IMAP access is disabled"

- 前往 Gmail 设置 → 转发和 POP/IMAP → 启用 IMAP

### Q: 找不到 "应用专用密码" 选项

- 必须先开启两步验证才能看到此选项
- 访问 https://myaccount.google.com/signinoptions/two-step-verification 开启

### Q: 安全性如何？

- 应用专用密码只能用于 IMAP 登录，不能用于修改账号设置
- 可以随时在 Google 账号设置中撤销应用专用密码
- 建议为每个应用生成独立的应用专用密码
- 密码存储在本地 `.env` 文件中，不会被提交到 git（已添加到 `.gitignore`）

---

## 相关链接

- [Gmail IMAP 设置帮助](https://support.google.com/mail/answer/7126229)
- [Google 账号安全设置](https://myaccount.google.com/security)
- [应用专用密码说明](https://support.google.com/accounts/answer/185833)
