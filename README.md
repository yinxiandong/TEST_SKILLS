# TEST_SKILLS

可独立安装的技能集合。一个技能一个目录，每个目录包含自己的规则、脚本及必要资源；可以只安装其中一个技能。

## 技能目录

| 技能 | 用途 | 依赖 | 入口 |
| --- | --- | --- | --- |
| `pms-test-case-authoring` | 根据 PMS 或本地需求生成、复用和优化用例，输出固定 31 列 Excel/CSV 与 PMS 映射 | Python 3.10+；Excel 需 openpyxl；访问 PMS 需自己的账号及工具 | [SKILL.md](pms-test-case-authoring/SKILL.md) |

当前仅包含以上一个独立技能。新增技能后，在此表补充用途、依赖和入口。生成本地用例不代表执行测试或登记 PMS，相关操作按用户明确要求开展。

## 只安装一个技能

下载或克隆本仓库，然后只复制选中的完整技能目录。无需安装其他技能，也无需复制仓库级的 `scripts/`、`docs/` 或离线压缩包。

在仓库根目录运行以下 PowerShell 示例，将现有技能安装到 Codex 用户技能目录；目标已存在时停止，避免混合覆盖：

```powershell
$skillName = 'pms-test-case-authoring'
$source = Join-Path (Get-Location).Path $skillName
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillsRoot = Join-Path $codexRoot 'skills'
$destination = Join-Path $skillsRoot $skillName
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) { throw '请在仓库根目录执行，并选择有效技能目录' }
if (Test-Path -LiteralPath $destination) { throw '目标已存在，请先检查已有安装和链接并备份，再升级' }
New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Recurse
```

Claude Code 用户可将同一个完整技能目录复制到 `~/.claude/skills/`。安装后新建会话，确认技能已出现再调用。可用下面的自然语言请求让支持技能安装的助手按目录安装：

> 从 GitHub 仓库 yinxiandong/TEST_SKILLS 中，只安装 pms-test-case-authoring 目录对应的技能。

技能若有 Python 依赖，在自己选定的虚拟环境中安装所选技能的 `requirements.txt`。例如，在仓库根目录为本地验证安装：

```bash
python -m pip install -r pms-test-case-authoring/requirements.txt
```

调用示例：

> 使用 $pms-test-case-authoring，根据 PMS 需求〈需求编号〉生成用例，输出到〈测试用例目录〉。先只生成本地文件。

### 更新方式

- 复制安装：拉取源码不会更新已安装副本。先检查并备份原目录，再用新版本完整替换，避免残留旧文件。
- 链接安装：如果技能发现目录是指向源码的符号链接或 Junction，源码变动会直接影响技能。先检查本地修改，再更新仓库。
- 新增技能需要单独安装；更新仓库不会自动把所有同级技能注册到工具中。

## 验证现有技能

从仓库根目录执行。示例数据仅用于验证格式，不是真实业务用例：

```bash
python pms-test-case-authoring/scripts/case_tools.py doctor
python pms-test-case-authoring/scripts/case_tools.py validate --input pms-test-case-authoring/assets/cases.example.json
python pms-test-case-authoring/scripts/case_tools.py build --input pms-test-case-authoring/assets/cases.example.json --output-dir ./demo-workspace/DEMO-00001
```

再次生成时使用新的输出目录，工具拒绝覆盖历史。真实需求资料与生成产物存放在用户工作区，技能目录仅保存规则、工具和公开示例。

## 维护多个技能

继续在仓库根目录添加并列技能目录，已有技能路径保持稳定。新增方式、最小示例和检查清单见 [CONTRIBUTING.md](CONTRIBUTING.md)。

仓库维护者可批量校验所有技能，或者只校验一个目录：

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate-repo.py
python scripts/validate-repo.py --skill pms-test-case-authoring
python -m unittest discover -s tests -v
```

仓库校验工具及开发依赖无需随单个技能安装。结构校验通过不代表业务覆盖完整或自动化执行通过。

## 其他资料

- [AutoCode 历史离线安装说明](docs/autocode-offline-install.md)
- [前端 UI 测试工作流参考](cvc-front-ui-test-workflow.md)
- `autocode-offline-package.zip`：保留的离线包，独立技能安装不依赖它。
