# AutoCode 插件离线安装指南

适用于无法访问外网或内网 GitLab 的环境，通过手动复制缓存文件完成安装。

## 前提条件

- 目标机器已安装 Claude Code
- 有一台能访问 `http://gitlab.allcam.com.cn` 的机器（用于下载）

---

## 方法一：复制插件缓存目录（推荐）

### 第一步：在有网络的机器上获取插件

```bash
# 克隆 autocode marketplace 仓库
git clone http://gitlab.allcam.com.cn/dev-flow/autocode-marketplace.git
```

或者直接打包已安装机器上的缓存目录：

```bash
# Windows（PowerShell）
Compress-Archive -Path "$env:USERPROFILE\.claude\plugins\cache\autocode-marketplace" -DestinationPath autocode-cache.zip

# Linux / macOS / WSL
tar -czf autocode-cache.tar.gz ~/.claude/plugins/cache/autocode-marketplace
```

### 第二步：将文件传输到离线机器

通过 U 盘、局域网共享、SCP 等方式将压缩包传输到目标机器。

### 第三步：解压到缓存目录

```bash
# Windows（PowerShell）
Expand-Archive -Path autocode-cache.zip -DestinationPath "$env:USERPROFILE\.claude\plugins\cache\"

# Linux / macOS / WSL
tar -xzf autocode-cache.tar.gz -C ~/.claude/plugins/cache/
```

解压后目录结构应为：

```
~/.claude/plugins/cache/autocode-marketplace/
└── autocode/
    └── 1.1.1/
        ├── INSTALL.md
        ├── agents/
        ├── commands/
        ├── scripts/
        └── skills/
```

### 第四步：配置 settings.json

编辑 `~/.claude/settings.json`，添加以下内容：

```json
{
  "extraKnownMarketplaces": {
    "autocode-marketplace": {
      "source": {
        "source": "git",
        "url": "http://gitlab.allcam.com.cn/dev-flow/autocode-marketplace.git"
      }
    }
  },
  "enabledPlugins": {
    "autocode@autocode-marketplace": true
  }
}
```

> 注意：`url` 字段填写原始仓库地址即可，插件管理器检测到本地缓存后不会发起网络请求。

### 第五步：验证安装

重启 Claude Code，执行：

```bash
ls ~/.claude/plugins/cache/autocode-marketplace/autocode/
```

能看到版本目录（如 `1.1.1`）即表示安装成功。

---

## 方法二：脚本安装（需要 WSL 或 Linux 环境）

如果目标机器可以运行 bash，先从有网络的机器下载安装脚本和插件包，再离线执行。

```bash
# 项目级安装（仅对当前项目生效）
./install-autocode.sh --project

# 用户级安装（对所有项目生效）
./install-autocode.sh --user
```

安装脚本位于 marketplace 仓库根目录。

---

## 升级

将新版本的缓存目录复制到对应路径，目录名改为新版本号即可：

```
~/.claude/plugins/cache/autocode-marketplace/autocode/<new-version>/
```

---

## 常见问题

**Q: 插件加载后 skills 不生效？**

检查 `settings.json` 中 `enabledPlugins` 是否包含 `"autocode@autocode-marketplace": true`。

**Q: 如何确认当前安装的版本？**

```bash
ls ~/.claude/plugins/cache/autocode-marketplace/autocode/
```

**Q: 多台机器如何统一管理？**

将整个 `~/.claude/plugins/cache/autocode-marketplace` 目录纳入内网文件服务器，各机器从内网地址下载解压即可。

---

## 目录结构说明

| 目录        | 说明                     |
| ----------- | ------------------------ |
| `agents/`   | AI 智能体定义文件        |
| `skills/`   | 技能包（slash commands） |
| `commands/` | 命令集                   |
| `scripts/`  | 辅助脚本                 |
