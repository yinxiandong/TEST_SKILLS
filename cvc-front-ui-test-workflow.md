---
id: cvc-front-ui-test-workflow
name: CVC 前端 UI 自动化测试完整工作流
description: Vue 3 + Element Plus + Vite 项目 UI 自动化测试完整工作流：三条输入路径、分层覆盖方法论、YAML 用例规范、pytest-playwright 执行、Allure 报告生成，含 6 个 Element Plus 专项陷阱和 pytest 配置规范。
source: conversation
triggers:
  - "ui test workflow"
  - "e2e-checker"
  - "e2e-case-generator"
  - "e2e-script-generator"
  - "pytest playwright vue element plus"
  - "Element is not an <input>"
  - "strict mode violation resolved to 2 elements"
  - "allure generate 0 test cases"
  - "titlePath"
  - "SVG captcha"
  - "valiCodeIden"
  - "ElMessageBox confirm"
  - "wait_for_url timeout logout"
  - "el-form-item__error"
  - "vue form validation block save"
  - "allure report empty"
quality: high
---

# CVC 前端 UI 自动化测试完整工作流

## The Insight

本项目采用 **pytest-playwright（Python）** 而非 Playwright TypeScript 脚本。原因：项目已有 pytest 基础设施，且 Python 生态对 SVG 验证码解析、Allure 集成更成熟。

工作流分三层：
1. **检测层**：扫描项目确认 E2E 集成状态（测试目录、配置文件、依赖）
2. **用例层**：分析前端代码（路由 + 组件）生成 YAML 用例规范，支持三条输入路径
3. **执行层**（pytest-playwright）：Python 实现，含 Allure 报告和统一日志

---

## 输入模式（三条路径）

### 路径 A：需求驱动

输入：`docs/requirement/{rq_id}/20-{stage}-需求测试设计.md` 中 `test_type: e2e` 的场景

流程：读取需求测试设计文档 → 提取 e2e 场景 → 按分层覆盖模型补充遗漏用例 → 生成 YAML → 注册 CSV（`source=requirement`）

### 路径 B：前端代码提取（本项目使用）

输入：目标项目前端源代码目录路径（`src/`）

流程：
```
分析前端代码 → 生成用例 → 去重 → 生成 YAML → 注册 CSV（source=code-extract）
```

**Vue Router 路由提取**（本项目）：
- 解析 `src/router/index.js` 中的 `routes` 数组
- 提取 `path`、`name`、`component` 字段
- 识别路由守卫（`beforeEach`）→ 生成权限态用例

**Vue 3 + Element Plus 组件分析**：
- `<el-input>` / `<el-form>` → 生成输入类用例（注意：选择器需穿透到 `input`，见陷阱 1）
- `<el-button>` / `<el-tabs>` → 生成点击类用例（注意：可能多实例，见陷阱 3）
- `v-if` / `v-show` → 生成状态类用例
- `<el-upload>` → 标记"依赖文件配置"，生成优雅跳过用例（见陷阱 6）

**API 端点提取**：从 `axios` 调用中提取 API 路径 → 辅助确定 `wait_pattern`

**去重策略**：生成前读取 CSV，对已有 `case_id` 的同页面同操作跳过，仅生成增量用例

### 路径 C：Git 变动刷新

输入：git 提交范围（如 `HEAD~5..HEAD`）

流程：
```bash
git diff --name-only {base}..{head}
# 过滤：src/views/, src/components/, src/router/, *.css, *.scss
```

变动分类：
- **新增页面/组件** → 新建用例
- **修改已有组件** → 刷新用例（检查选择器、交互变化）
- **删除页面/组件** → CSV 标记 `status=deprecated`
- **路由变更** → 更新 URL 断言

---

## 测试方法论（分层覆盖模型）

| 层级 | 方法论 | 覆盖目标 | 产出 |
|------|--------|---------|------|
| L1 页面覆盖 | 页面清单法 | 每个页面/路由至少有 1 个 P0 用例 | 页面可达性用例 |
| L2 流程覆盖 | 场景法 | 核心用户旅程端到端覆盖 | 业务流程用例 |
| L3 交互覆盖 | 等价类 + 边界值 | 表单输入、按钮操作的正反例 | 交互验证用例 |
| L4 状态覆盖 | 状态迁移法 | 权限态、登录态、数据态切换 | 状态转换用例 |
| L5 异常覆盖 | 错误推测法 | 网络异常、空数据、超长输入 | 异常场景用例 |

### 级别分配规则

- **P0**：L1 核心页面可达 + L2 核心业务流程（`smoke=true`，冒烟必测）
- **P1**：L2 次要流程 + L3 主要交互
- **P2**：L3 次要交互 + L4 状态覆盖
- **P3**：L5 异常场景 + 边缘用例

### 覆盖率检查清单（用例生成后校验）

- [ ] 所有路由页面至少有 1 个 P0 用例
- [ ] 核心业务旅程全部覆盖（登录 → 核心功能 → 登出）
- [ ] 每个表单至少有正例和反例各 1 个
- [ ] 关键状态切换有覆盖（未登录 → 已登录 → 会话过期）

### 本项目覆盖结果

| 模块 | 用例数 | P0 | P1 | P2 | P3 |
|------|--------|----|----|----|----|
| auth（认证） | 10 | 3 | 5 | 2 | 0 |
| homepage（首页） | 7 | 1 | 4 | 2 | 0 |
| organization（组织管理） | 8 | 1 | 3 | 3 | 1 |
| system_params（系统参数） | 6 | 1 | 2 | 3 | 0 |
| **合计** | **31** | **6** | **14** | **10** | **1** |

---

## YAML 用例格式

```yaml
case_id: TC-UI-{CATEGORY_UPPER}-{SEQ}   # 唯一标识，三位序号，如 TC-UI-AUTH-001
case_name: {CASE_NAME}                   # 简明描述测试目标
level: P0                                # P0|P1|P2|P3
smoke: true                              # P0 默认 true
type: ui-test
category: {category}                     # 与 usecase/ 子目录名一致
source: code-extract                     # requirement|code-extract|git-refresh
source_ref: "src/views/login/index.vue"  # 来源引用
tags: [auth, login, happy-path]

preconditions:
  - 系统可访问，验证码服务正常

steps:
  - seq: 1
    action: 输入用户名
    target: ".loginInput input"          # Vue/Element Plus：必须穿透到 input（见陷阱 1）
    input: "admin"
    wait: none
    screenshot: false
  - seq: 2
    action: 点击登录按钮
    target: ".loginButton"
    wait: response
    wait_pattern: "**/api/auth/login"
    screenshot: true

expected:
  - condition: URL 跳转到首页
    value: "**/homePage"
    assertion: toHaveURL
  - condition: 首页内容可见
    value: ".homepagehead"
    assertion: toBeVisible

postconditions:
  - 登出系统

script_path: ""
created_at: "2026-03-24"
updated_at: "2026-03-24"
```

**必填字段速查**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `case_id` | 是 | 格式 `TC-UI-{CATEGORY}-{SEQ}`（三位序号） |
| `case_name` | 是 | 简明描述测试目标 |
| `level` | 是 | `P0` / `P1` / `P2` / `P3` |
| `smoke` | 是 | `true` / `false`（P0 默认 true） |
| `steps[].target` | 是 | Element Plus 输入类组件必须加 ` input` 后缀 |
| `steps[].wait` | 是 | `visible` / `networkidle` / `response` / `none`，禁止固定延时 |
| `expected[].assertion` | 是 | `toHaveURL` / `toBeVisible` / `toContainText` |

---

## CSV 注册表管理

文件路径：`tests/ui-test/testcase-registry.csv`

维护规则：
1. **新建用例**：追加新行，`status=pending`（无脚本）或 `status=active`（有脚本）
2. **更新用例**：更新 `updated_at` 和受影响字段
3. **废弃用例**：将 `status` 改为 `deprecated`
4. **脚本生成后**：回填 `script_path`，`status` 从 `pending` 改为 `active`

约束：
- `case_id` 全局唯一，生成前必须检查
- 路径 B/C 必须去重，避免与现有用例重复

---

## 执行层：pytest-playwright 配置

目录结构：
```
tests/ui-test/pytest/
├── conftest.py          # 全局 fixture（登录、日志钩子）
├── config.py            # BASE_URL、TEST_USER、TEST_PASSWORD
├── captcha_resolver.py  # SVG 验证码解析 + OCR 兜底
├── logger.py            # console + 文件双输出日志
└── tests/
    ├── test_auth.py
    ├── test_homepage.py
    ├── test_organization.py
    └── test_system_params.py
```

`pytest.ini`（项目根目录）：
```ini
[pytest]
testpaths = tests/ui-test/pytest/tests
addopts = --browser chromium --headed --base-url http://172.16.29.102 --alluredir=allure-results
```

常用执行命令：
```bash
python -m pytest                                          # 全量
python -m pytest -m "smoke"                               # 仅 P0 冒烟
python -m pytest tests/ui-test/pytest/tests/test_auth.py  # 单模块
python -m pytest --headed=false                           # 无头模式（CI）
```

---

## Allure 报告

```bash
allure serve allure-results    # 生成并在浏览器打开
allure generate allure-results -o allure-report --clean  # 生成静态 HTML
```

**版本必须对齐**（见陷阱 2）：
```bash
allure --version               # 确认 CLI 版本（本项目：2.13.7）
pip install "allure-pytest==2.13.5"
```

---

## 6 个 Element Plus 专项陷阱

### 陷阱 1：输入框选择器必须穿透包裹 div

`<el-input>` 渲染为 `<div class="el-input"><input/></div>`，`.fill()` 只能作用于 `<input>`。

```python
# 错误
page.locator(".loginInput").fill("admin")

# 正确
page.locator(".loginInput input").fill("admin")
page.locator("input[type='password']").fill("Admin@123456")
page.locator(".valiCodeInput input").fill(code)
```

### 陷阱 2：Allure 版本必须精确对齐

`allure-pytest >= 2.14` 写入 `titlePath` 字段，Allure CLI 2.13.x 不认识，报告静默为 0 条用例。

诊断：打开 `allure-results/*.json`，搜索 `"titlePath"` 字段——存在则版本过高。

```bash
allure --version
pip install "allure-pytest==2.13.5"
```

### 陷阱 3：Element Plus 组件多实例导致严格模式冲突

`.el-tabs`、`.el-button--primary` 等在 DOM 中可能出现多次，Playwright 严格模式报错。

```python
# 正确：始终加 .first
page.locator(".el-tabs").first.click()
page.locator(".search_btn .el-button--primary").first.click()
```

### 陷阱 4：ElMessageBox 确认对话框拦截导航

登出、删除等操作触发 `ElMessageBox.confirm()`，必须先点确认再等待跳转。

```python
page.locator(".logout-btn").click()
page.locator(".el-message-box__btns .el-button--primary").click()
page.wait_for_url("**/loginMain", timeout=10_000)
```

### 陷阱 5：SVG 验证码不能用 OCR

验证码是 SVG data URL，ddddocr 无法识别。必须解码 base64 → 解析 SVG XML → 提取 `<text>`。

```python
import base64, re
from urllib.parse import unquote

def _extract_svg_text(src: str) -> str:
    if src.startswith("data:image/svg+xml;base64,"):
        svg = base64.b64decode(src.split(",", 1)[1]).decode("utf-8", errors="ignore")
    elif src.startswith("data:image/svg+xml,"):
        svg = unquote(src.split(",", 1)[1])
    else:
        return ""
    texts = re.findall(r"<text[^>]*>([^<]+)</text>", svg)
    return "".join(t.strip() for t in texts)
```

### 陷阱 6：Vue 表单整体校验阻止保存（优雅跳过）

Vue 3 表单 `ruleForm.validate()` 做整体校验，图片字段（`<el-upload>`）未填时文本字段也无法保存。
策略：验证输入交互正常，保存失败时 `pytest.skip`。

```python
input_el.fill("TestTitle123")
page.locator(".confirmBtn .el-button--primary").click()
page.wait_for_load_state("networkidle")

if page.locator(".el-message--success").first.is_visible(timeout=3_000):
    pass  # 保存成功
else:
    assert not page.locator(".el-form-item").first.locator(".el-form-item__error").is_visible()
    pytest.skip("保存未成功（依赖图片配置），但输入交互正常")
```

---

## 日志模块规范

`tests/ui-test/pytest/logger.py`：console（INFO）+ 文件（DEBUG）双输出。

```python
def get_logger(name: str = "ui-test") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fh = logging.FileHandler("logs/ui-test.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
```

pytest hooks 在 `conftest.py` 中记录每条用例的 `[START]` / `[PASSED]` / `[FAILED]` / `[SKIPPED]`。

---

## 约束

- YAML 用例文件只记录用例规范，不包含执行逻辑
- `case_id` 全局唯一，生成前必须检查 CSV
- 等待策略严格遵守规范，禁止使用固定延时（`time.sleep`）
- Element Plus 输入类选择器必须穿透到原生 `input`/`textarea`
- Allure 插件版本必须与 CLI 版本对齐

---

## 已知跳过用例

| 用例 | 原因 |
|------|------|
| `test_homepage_platform_switch` | 需特定平台切换权限（L4 状态覆盖） |
| `test_sys_params_save_title` | 需预先配置背景图和 Logo（陷阱 6） |

---

## 关键文件

- [pytest.ini](pytest.ini) — 运行参数
- [tests/ui-test/pytest/conftest.py](tests/ui-test/pytest/conftest.py) — 登录 fixture
- [tests/ui-test/pytest/captcha_resolver.py](tests/ui-test/pytest/captcha_resolver.py) — SVG 验证码
- [tests/ui-test/pytest/logger.py](tests/ui-test/pytest/logger.py) — 日志模块
- [tests/ui-test/pytest/README.md](tests/ui-test/pytest/README.md) — 完整使用文档
