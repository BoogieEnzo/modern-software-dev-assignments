# Week 9 Plan: Repo Trends Explorer

## 产品定位（已确认）
每天给用户推荐 **3 个值得关注的 GitHub 仓库**。
产品形态是 **前端每日简报页面**：用户打开固定网址即可看到当日结果。
首版采用 **通用热度型**，不做个性化。
用户范围先不设限制（先做通用可用版本）。

## 老板决策（已确认）
- 首页信息密度：标准版（3 张卡片 + 关键指标）
- 推荐理由风格：编辑风（一句话说明“为什么值得关注”）
- 内容过滤：过滤 GitHub 标记的成人/敏感内容仓库
- 语言范围：全语言
- 当日更新失败策略：直接显示“暂时无法更新”（不回退历史）
- 验收优先级：数据准确、页面体验、稳定可用并列第一优先
- 版本节奏：2 周交付稍完整版本（非 1 周极简 MVP）

## 核心目标（MVP）
- 用户每天打开页面，能看到当日 Top 3 热门增长仓库
- 推荐标准透明、可解释、可复现
- 页面实时展示最新榜单结果（打开网页自动显示）

## 排名口径（已确认）
主指标：**7 天累计增星**

定义：
- `weekly_star_gain = stars_today - stars_7d_ago`

排序：
1. 按 `weekly_star_gain` 降序
2. 若并列，按 `updated_at` 新到旧
3. 若仍并列，按 `stars_today` 降序

## 入榜规则（当前默认）
- 仅公开仓库
- 排除 archived 仓库
- 过滤成人/敏感内容仓库
- 最低星标门槛：`stars_today >= 200`（可配置）

## 新仓库规则（已确认）
- 新仓库（创建不足 7 天）参与主榜
- 计算方式：`weekly_star_gain = stars_today - stars_at_creation`
- 说明：对新仓库等价于“创建以来累计增星”

## MVP 功能范围
1. 每日榜单页（Top 3）
2. 仓库卡片字段展示
3. 每日实时更新数据并展示
4. 每条推荐附一句话理由（为什么值得关注）

暂不纳入 MVP：
- 复杂趋势曲线
- GraphQL 深度分析
- 历史记录/历史榜单
- 个性化推荐
- 反馈偏好（如“减少类似推荐”）

## 核心页面
1. `/` 首页（每日简报：当日 Top 3 + 一句话理由）

## API 设计（MVP）
```http
GET /api/trending/today
```

可选内部任务接口（仅服务端使用）：
```http
POST /api/internal/snapshot/run
```

## 数据模型（建议）
### `repo_snapshots`
- `id`
- `snapshot_date` (date)
- `owner`
- `repo`
- `full_name`
- `description`
- `language`
- `stars_today`
- `stars_7d_ago`
- `weekly_star_gain`
- `forks`
- `updated_at`
- `repo_url`
- `archived`
- `created_at`

## 数据来源
- GitHub REST API（首版）
- GraphQL（后续优化时再引入）

## 刷新策略
- 每天固定时间抓取一次（如 UTC 00:10）
- 保存当日快照，避免页面实时请求 GitHub 导致限流
- 若抓取失败，前端显示“暂时无法更新”，并记录错误日志

## 成功标准（MVP 验收）
1. 用户打开页面时可看到最新 Top 3 榜单
2. 排名计算可通过日志复核
3. 每条推荐都包含一句话推荐理由
4. 接口在无 GitHub 可用性问题时成功率 >= 99%
5. 页面默认展示标准信息密度（关键指标完整）
6. 敏感内容仓库不会进入推荐结果

## 三 Agent 分工（执行版）
### Agent 1: 前端
- 实现每日简报首页（Top 3 卡片）
- 每卡片展示：仓库名、描述、语言、stars、7日增星、forks、更新时间、推荐理由
- 状态处理：加载中、空结果、更新失败（显示“暂时无法更新”）
- 保证桌面/移动端可读性

### Agent 2: 后端
- 实现 `GET /api/trending/today`
- 接入 GitHub REST API，计算 `weekly_star_gain`
- 应用入榜过滤规则（公开、非 archived、非敏感、星标门槛）
- 生成编辑风一句话推荐理由
- 提供日志用于排名可追溯与问题排查

### Agent 3: 测试
- API 测试：正常返回、空数据、第三方异常、过滤规则命中
- 排名测试：7 天累计增星排序与并列处理
- 前端验收测试：关键指标展示、错误态文案、移动端展示
- 回归清单：数据准确/页面体验/稳定可用三目标并行验收

## 技术实现方向
### Stack A (Bolt - Next.js + TS + Prisma)
- 作为快速全栈实现方案
- 前端展示每日简报榜单
- Prisma + SQLite 存储快照

### Stack B (Python - FastAPI)
- Python 后端实现数据抓取、计算和 API
- 可搭配简单前端（HTMX 或分离）

### Stack C (Go - Gin/Chi)
- Go 实现轻量 API 服务
- 以学习 Go 与对比开发体验为目标

## 交付物
- 3 个独立项目文件夹 (`stack-a/`, `stack-b/`, `stack-c/`)
- 每个包含完整代码 + `README.md`
- `writeup.md`：比较三栈实现差异（开发效率、性能、维护性）
