# ImgBatch 官方网站

基于 Vite + React + Tailwind 的静态落地页（v3.0），用于产品介绍与下载引导。

## 本地开发

```bash
cd website
npm install
npm run dev
```

浏览器访问 http://localhost:5174

## 构建

```bash
npm run build
npm run preview
```

## 部署到 Vercel

Vercel 生产环境通常**固定部署 `main` 分支**（无法在部分套餐下改分支）。官网代码已合并进 `main`，推送 `main` 即可触发部署。

1. 在 [Vercel](https://vercel.com) 导入仓库（或已有项目等待自动部署）
2. 项目设置中指定 **Root Directory** 为 `website`
3. Framework Preset 选择 **Vite**（或留空，由 `vercel.json` 自动识别）
4. Production Branch 保持 **main**（默认）
5. Build Command: `npm run build` · Output Directory: `dist`

### 环境变量

当前站点为纯静态页，无需环境变量。后续若接入分析或 API，可在 Vercel 项目设置中添加。

### 自定义域名

在 Vercel 项目 → Settings → Domains 中绑定你的域名即可。

## 内容维护

- 文案与链接：`src/content.ts`
- 页面结构：`src/App.tsx` 与各 `components/` 文件
- 品牌色与字体：`src/styles/globals.css`（与 `design-system/imgbatch/MASTER.md` 一致）

## 下载链接

默认指向 GitHub Releases 最新页。发布安装包后，可在 `content.ts` 的 `SITE.releases` 中改为具体资产 URL。
