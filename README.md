# script.arcticfuse.focus

Arctic Fuse 3 皮肤的可选聚焦助手：在 OSD 播放列表与海报墙中，把焦点定位到正在播放或上次播放的剧集。

皮肤端不是硬依赖——未安装本插件时皮肤照常运行，只是不会自动定位。

## 安装

1. 下载 [最新 release](https://github.com/caiwx86/script.arcticfuse.focus/releases/latest) 里的 `script.arcticfuse.focus-<version>.zip`
2. Kodi → 插件 → 从 zip 安装
3. 无需重启，打开播放列表 / 海报墙即生效

## 皮肤端调用

```xml
<!-- 打开 OSD 播放列表时直接带焦点（无跳变） -->
<ondown condition="System.HasAddon(script.arcticfuse.focus)">RunScript(script.arcticfuse.focus,open,1140,7000)</ondown>
<ondown condition="!System.HasAddon(script.arcticfuse.focus)">ActivateWindow(1140)</ondown>

<!-- 兜底：窗口以其它方式打开时再补一次定位 -->
<onload condition="System.HasAddon(script.arcticfuse.focus)">RunScript(script.arcticfuse.focus,playlist,7000)</onload>

<!-- 海报墙（容器 id = 视图 id，如 512） -->
<onfocus condition="System.HasAddon(script.arcticfuse.focus)">RunScript(script.arcticfuse.focus,wall,$PARAM[id])</onfocus>
```

## 行为

### open 模式

以 `ActivateWindowAndFocus(window, control, index)` 打开窗口：窗口出现时焦点已经在正在播放的条目上，没有可见跳变。

### playlist 模式

| 步骤 | 说明 |
|---|---|
| 1 | 等目标容器出现条目（最多 3 秒，100ms 轮询），避免列表异步绑定把光标重置 |
| 2 | 读 `VideoPlayer.PlaylistPosition`（1 起算），换算成 0 起算索引 |
| 3 | 执行 `SetFocus(<control>, <index>, absolute)` 按绝对位置定位 |
| 4 | `PlaylistLength <= 1`（季视图回退）时不做任何操作 |

### wall 模式

| 步骤 | 说明 |
|---|---|
| 1 | 从墙上首个条目的 DBID 反查 `tvshowid` / `season` |
| 2 | `VideoLibrary.GetEpisodes` 取该季剧集（按集数升序） |
| 3 | 优先聚焦**正在播放**的剧集；否则聚焦 `lastplayed` 最近的剧集 |
| 4 | 已在该项上则不重复聚焦；非剧集列表（电影墙/演员墙）自动无操作 |

## 兼容性

- Kodi 19+（`xbmc.python` 3.0.0），在 Kodi 21 Omega 上开发与验证
- 纯 Python 标准库 + Kodi 内置 JSON-RPC，无第三方模块
- 所有失败都会静默跳过（只写日志），不会影响播放

## 已知边界

- 墙视图按「集数升序」计算索引；如果季视图改成其它排序，索引可能偏移
- 墙视图触发时机是容器获得焦点时；已在目标海报上时不会重复跳转

## 许可证

MIT，见 [LICENSE](LICENSE)。
