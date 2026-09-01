# 发票台账助手

## 功能介绍

- 上传销售发票或采购发票的 PDF、图片文件。
- 调用 Dify 工作流识别发票号码、开票日期、购销双方、金额、订单号和商品明细。
- 自动校验未税金额、税额与价税合计，并标记需要人工复核的内容。
- 由业务人员补充账期、预付款、累计收付款金额、负责人和复核状态。
- 使用 SQLite 保存发票台账，并阻止同一发票号码重复入账。
- 支持一张发票关联多个订单，同一张发票内的重复订单号会自动去重。
- 支持按单据类型、收付款状态、发票号、往来单位和订单号查询台账。
- 自动计算未收款、部分收款、已收款、未付款、部分付款和已付款状态。
- 根据到期日生成即将到期、今日到期和已逾期提醒。
- 支持通过钉钉自定义机器人发送账期提醒。

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

3. 在项目根目录创建 `.env`，填写以下配置：

   ```env
   DIFY_API_BASE_URL=http://127.0.0.1:18082/v1
   DIFY_API_KEY=填写Dify应用API密钥
   DIFY_USER=invoice-ledger-local

   DINGTALK_WEBHOOK=填写钉钉机器人Webhook地址
   DINGTALK_SECRET=填写钉钉机器人加签密钥
   ```

4. 如果 Dify 部署在远程服务器，另开一个 PowerShell 窗口并建立 SSH 隧道：

   ```powershell
   ssh -N -L 18082:127.0.0.1:18082 <服务器用户名>@<服务器地址>
   ```

   运行程序期间需要保持这个 SSH 窗口开启。

5. 启动 FastAPI：

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

6. 浏览器访问：

   ```text
   业务页面：http://127.0.0.1:8000/
   API 文档：http://127.0.0.1:8000/docs
   ```
