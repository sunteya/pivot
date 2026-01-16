# Pivot

Pivot 是一个基于 [Flet](https://flet.dev) 构建的 **Windows 桌面应用程序**，专注于高效的目录与版本管理。

它主要用于管理本地软件或资源的多个版本目录，通过**软链接（Symlink/Junction）**机制建立统一的访问入口，让你能够轻松地在不同版本之间进行切换、回滚或更新，而无需反复移动文件或修改外部引用路径。

## 核心机制 (Core Concept)

Pivot 的设计哲学是将**实体文件版本**与**访问入口**分离：

1.  **实体存储 (Versions)**: 所有的具体版本目录都物理存储在 `Versions` 文件夹下。
2.  **统一入口 (Persists)**: 在 `Persists` 目录下建立指向特定版本的符号链接（快捷方式）。

### 目录结构示例

```text
Root/
├── Versions/                  # 存放所有物理文件
│   ├── Bandizip-7.30/         # 旧版本实体
│   ├── Bandizip-7.40/         # 新版本实体
│   └── Nodejs-14.0.0/
│
└── Persists/                  # 对外暴露的统一路径 (Symlinks)
    ├── Bandizip -> ..\Versions\Bandizip-7.40  # 当前指向 7.40 版
    └── Nodejs   -> ..\Versions\Nodejs-14.0.0
```

### 工作流程

当需要更新版本（例如从 Bandizip 7.30 切换到 7.40）时，Pivot 不会覆盖文件，而是执行以下操作：
1.  将新版本放置于 `Versions/Bandizip-7.40`。
2.  移除 `Persists/Bandizip` 旧的指向链接。
3.  新建 `Persists/Bandizip` 链接指向 `Versions/Bandizip-7.40`。

这种方式确保了：
*   **原子性切换**: 版本更替通过修改链接瞬间完成。
*   **版本隔离**: 不同版本的文件物理隔离，互不干扰。
*   **路径稳定**: 外部只需引用 `Persists/Bandizip`，无需关心当前具体使用的是哪个版本号。

---

## Run the app

### uv

Run as a desktop app:

```
uv run flet run
```

For more details on running the app, refer to the [Getting Started Guide](https://docs.flet.dev/).

## Build the app

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://docs.flet.dev/publish/windows/).
