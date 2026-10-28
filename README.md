# 投资情报中心

中文个人投资资讯网站。Python 增量采集 + 纯静态 HTML/CSS/JavaScript + JSON + GitHub Actions + GitHub Pages。无需服务器、域名或前端构建工具。电脑关机后，GitHub 调度仍可运行。

## 当前交付状态（2026-10-28）

这是可运行的 MVP，**不是已验证上线的完整情报服务**。

- 已实现：七类可配置关注领域、RSS 独立采集、条件请求与访问间隔、URL/标题/数值保守去重、稳定事件 ID、多来源链接、原 URL 内容更新标记、月归档、搜索/日期/分类/重要性筛选、明暗主题、手机布局、AI 费用和重试限制、JSON Schema、无 AI 降级。
- 已实现工作流：UTC `7,17,27,37,47,57 * * * *`，手动采集、串行增量持久化、Pages 官方部署、测试。全部来源失败会明确失败，不将触发成功当成采集成功。
- **真实来源验证未通过**：美联储、美国劳工统计局、欧洲央行、人民银行、国家统计局和深圳政府请求在当前云环境代理处受阻（美联储明确返回 CONNECT 403）。美联储和 BLS 已有 RSS 适配器，但无成功采集记录；其他来源明确标为未接入。公开数据目前没有任何新闻，未填充示例新闻。
- 11 项 Python 测试及系统 Chromium 桌面/手机交互测试通过。测试中的来源、AI 响应与事件为隔离夹具，不是联网成功证据。
- 未验证：真实 OpenAI Responses 调用、GitHub Actions 实际执行、Pages 线上访问。详见本次交付报告。
- 未实现：跨语言/语义事件聚合、不同 URL 下新增事实的自动归并、官方公告 HTML/API 适配、深圳红山成交数据、PHP/THB 行情、正式告警通知。相似标题仅在 72 小时内且数值一致时聚合；不同表述可能保留为不同事件，需要人工核实。

## 新手部署：现有仓库 111

1. 打开 GitHub 仓库 `salesguod-jpg/111`，确认代码位于默认分支 `main`；如果交付报告说明推送失败，在 GitHub 点击 **Add file → Upload files** 上传项目文件并提交到 main。隐藏的 `.github/workflows/` 也必须上传；浏览器上传不便时，可使用 GitHub Desktop：克隆仓库、复制本项目文件（不含 `.git`、`.venv`、`.runtime`）、Commit、Push。
2. 打开 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。不需要购买域名。
3. 打开 **Settings → Actions → General**，允许本仓库使用 GitHub Actions；组织策略需允许 `contents: write` 和官方 Pages Actions。仓库应为 Public，避免套餐限制。
4. 打开 **Actions → Tests** 检查测试。打开 **Collect news → Run workflow → main → Run workflow**，点进运行的 Collect 步骤查看 `successful_sources` 和摘要。只有来源状态 `ok` / `not_modified` 才表示来源请求成功；检查是否确实有新增事件。
5. 打开 **Actions → Deploy Pages → Run workflow** 完成首次部署。如果采集成功且公开内容有变化，后续会自动调用部署。无需每十分钟重建前端。
6. 部署成功后，在 Pages 设置中复制实际地址。此仓库预期地址为 **https://salesguod-jpg.github.io/111/**，当前尚未验证上线。所有资源使用相对路径，兼容仓库子目录。

需求示例的 `/investment-intelligence-hub/` 只有在仓库使用该名称时才适用。若希望使用该路径，请在 Settings → General → Repository name 重命名仓库，再检查 Pages 给出的地址；本项目无需修改 base path。

## OpenAI（可选）

无 Key 时采集与页面仍工作，不会把规则判断伪装成 AI 分析。

1. 在 OpenAI API 平台创建单独项目及 API Key，设置账户/项目预算与可用模型。**不要在聊天、代码、JSON 或普通变量中粘贴密钥。**
2. GitHub 仓库 **Settings → Secrets and variables → Actions → Secrets → New repository secret**：名称 `OPENAI_API_KEY`，值在 GitHub 安全输入。
3. 同页 **Variables → New repository variable**：名称 `OPENAI_MODEL`，填写你账户可用、支持 Responses API 与结构化输出的模型 ID。代码没有默认模型。
4. 修改 `config/settings.json` 的 `ai`：默认每日最多 10 次、估算软上限 0.20 美元、每个版本最多尝试两次。将输入/输出单价改成所选模型的官方每百万 Token 单价。每日按北京时间划分。
5. 手动运行 Collect news，核实 `AI 调用`、公开 `usage` 与事件模型/时间。欠费、401/403/429 会当日停止后续调用，新闻保留。恢复账户后次日重试，或在明确诊断后人工清除 `state/state.json` 对应 `quota_blocked_day`。

程序在网络请求前持久化次数和保守预留费用，失败也记账。公开统计记录实际返回 Token；API 未返回 usage 时 Token 无法获知，预留费用仍保留。预留费与实际费取较高值，因此统计可能高估费用。软上限**不能替代平台预算**，也无法保证模型单价配置正确或异常账单绝不超限。不得将代理占位 Key 拷贝到 GitHub；GitHub Secret 必须由你独立安全配置。

## 修改关注范围和采集频率

- `config/settings.json` → `topics`：`keywords` 是中英文关键词，`weight` 是优先顺序，`enabled` 控制启用。规则仅预筛选，避免把所有新闻送入 AI。
- `config/sources.json` 是 source registry：启用前需真实验证 RSS 格式、使用条件、频率、时间字段。`enabled:false` 的来源不会采集。只支持 `kind:rss` 的来源；HTML/API 需要后续实现解析器。
- `min_interval_minutes` 独立约束各来源：当前 Fed 最少 30 分钟，BLS 最少 60 分钟。每十分钟是调度检查频率，不强行对每站每十分钟抓取。
- 调度位于 `.github/workflows/collect.yml` 的 cron，**GitHub 使用 UTC**。北京时间 UTC+8；本 cron 每小时的分钟相同。计划任务可能延迟、漏跑；长时间无仓库活动（公开仓库通常 60 天）可能停用，须到 Actions 检查并重新启用。不是实时新闻 SLA。

## 数据与并发

- `site/data/archive/YYYY-MM.json`：按月保存事件，失败不清空历史。仅存来源标题、最多 400 字符短摘录、URL 与分析，不抓取或永久复制全文。
- `site/data/index.json`：最新 500 条、730 天内热索引；更老事件仍在月归档，可通过历史选择器加载。历史**不会自动删除**，应按版权要求和仓库体积人工评估。
- `state/state.json`：已见文章哈希、AI 尝试/预算、上次提交时的来源检查点；没有密钥。与新闻一起 Git 提交，不能把临时 runner 当永久数据库。
- `.runtime/feeds.json`：仅条件请求与访问间隔优化缓存。Actions cache 丢失会重新请求，不影响 Git 中的新闻和 AI 预算。
- 无公开内容变化且无 AI 调用时，不提交、不部署；本次状态通过 Actions 摘要与 14 天 artifact 保存。网页状态可能因此滞后，Actions 才是最新运行依据。
- 有内容变化或 AI 调用时，提交 state、status 和事件；只有首页内容变化才部署。GITHUB_TOKEN 自动提交不再触发 push 工作流，采集工作流显式调用可复用 Pages 工作流。
- concurrency 串行化采集；push 不使用强制覆盖。若你同时修改 main 导致 push 拒绝，任务失败并停止发布，下一次从远端最新数据重新采集。不要手工更改 AI 预算计数，避免重复计费。
- 单次数据预算 50 MB；Pages 工作流检查发布目录体积；定期运行 `git count-objects -vH` 查看 Git 大小，`du -sh site` 查看发布大小。长期运行 Git 历史也会增长，应人工维护。触及体积阈值会阻止发布而非删除旧数据。

## 查看故障和停止

- GitHub **Actions → Collect news → 最近运行 → Summary**：成功/失败来源、新增数和 AI 调用。详细日志只输出计数和错误类型，不输出 Key 或 API 响应。
- 同次运行的 **Artifacts → collection-status-...**：最新实际运行时间、最近成功时间、来源状态与每日用量。无计划触发时没有新的 artifact，检查 Actions 是否被禁用。
- 网站“运行状态与新闻来源”：随上次内容部署的状态。部署时间由 `deployed-at.txt` 记录（只有 Pages 工作流执行才生成部署时间）。
- 暂停：Actions → Collect news → 右上角 **… → Disable workflow**；恢复点击 Enable workflow。也可删除 cron，仅保留手动触发。删除 OpenAI Secret 只停止 AI，不停止采集。
- 新闻源结构变化、许可不清或被限制时，禁用该来源，不能突破登录、验证码、付费墙或反爬。

## 本地开发

```bash
cd /workspace/111
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/collect.py
python3 -m http.server 8000 --directory site
```

浏览器打开本地服务即可；这只是开发步骤，不是已经上线的地址。采集全部来源失败会以非零退出，历史仍保留。

可选浏览器测试（不属于生产依赖）：`pip install playwright==1.56.0`，安装系统 Chromium，运行 `python tests/browser_smoke.py`。当前测试先检查真实空数据界面，再用仅在浏览器内拦截的测试夹具检查详情；未把假新闻发布到 site。

## 费用

GitHub Public 仓库标准 Linux 托管 Actions 与 Pages 通常无固定费用，具体以当前账户规则为准。此计划约 144 次采集/天，依赖安装、工作流及数据增长仍占用 GitHub 资源。AI 按所选模型使用量计费；无 Key 不产生 AI 费用。没有付费数据库、常驻服务器或域名支出。
