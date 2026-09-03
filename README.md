# 供应链订单与发票台账助手

## 功能介绍

- 上传销售发票、采购发票以及销售订单、采购订单，调用 Dify Workflow 提取单据编号、日期、往来单位、金额、结算方式和关联订单等信息。
- 对金额、日期和必填字段进行自动校验，标记缺失内容及异常信息，并由业务人员人工确认后保存。
- 使用 SQLite 保存订单、发票、账期、预付款、累计收付款、负责人和复核状态。
- 根据订单号自动关联同方向的订单与发票，并避免同一订单号或发票号重复入账。
- 自动计算未收款、部分收款、已收款、未付款、部分付款和已付款状态。
- 在首页统一展示订单与发票账期预警，对已关联的同一笔业务合并重复提醒。
- 通过钉钉自定义机器人发送即将到期、今日到期和逾期提醒，并记录发送结果以避免重复通知。
- 支持订单与发票台账查询、人工更新以及统一 Excel 台账导出。
- 使用带签名和有效期的 HttpOnly Cookie 保护业务页面、API、Swagger 文档及 Excel 下载。

## 启动程序

1. 在 PowerShell 中进入项目目录：

   ```powershell
   cd D:\Agent\FPZS
   ```

2. 首次运行时创建虚拟环境并安装依赖：

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. 在项目根目录创建 `.env`，填写运行配置：

   ```env
   DIFY_API_BASE_URL=http://114.66.41.184:18082/v1
   DIFY_API_KEY=填写发票Workflow的API密钥
   DIFY_ORDER_API_KEY=填写订单Workflow的API密钥
   DIFY_USER=invoice-ledger-local

   DINGTALK_WEBHOOK=填写钉钉机器人Webhook地址
   DINGTALK_SECRET=填写钉钉机器人加签密钥
   REMINDER_HOUR=9
   REMINDER_MINUTE=0

   APP_USERNAME=manager
   APP_PASSWORD="填写至少8位的强密码"
   APP_SESSION_SECRET=填写至少32位的随机会话密钥
   APP_SESSION_HOURS=12
   APP_COOKIE_SECURE=false
   ```

   生成随机会话密钥：

   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   本地 HTTP 运行时使用 `APP_COOKIE_SECURE=false`；通过 HTTPS 部署后改为 `APP_COOKIE_SECURE=true`。

4. 启动 FastAPI：

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

5. 浏览器访问：

   ```text
   登录页面：http://127.0.0.1:8000/login
   业务页面：http://127.0.0.1:8000/
   API文档：http://127.0.0.1:8000/docs
   ```
