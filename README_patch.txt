logo 检测（1.2.0 起为真·图像数据检测）

- 读取图片头（本地文件或 HTTP Range 前 8KB），判断是否带 alpha 通道：
  - PNG：检查 IHDR 的 color type（4/6 带 alpha）与 tRNS 块
  - WebP：VP8X 的 alpha 标志或 ALPH 块
  - JPEG：没有 alpha 通道 → 判定为带黑底
  - 未知容器：默认可用，不拦截
- 结果写入 Window(Home).Property(ArcticFuse.Logo.Matted)，皮肤据此跳过带黑底的库 logo
- 结果按 URL 缓存 5 分钟；读取失败一律视为可用，绝不影响播放
