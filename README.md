# Social Science Empirical Research KB Skills

一套面向社会科学实证研究、重点支持定量研究的 Codex Skill 套件。它把 Zotero 作为文献与 PDF 权威源，把结构化 Evidence 作为证据层，并在 Obsidian 中维护文献笔记、论断、概念、比较矩阵、主题综述与研究地图。

## 组成

- `social-science-empirical-kb`：总控与状态机
- `social-science-literature-discovery`：文献检索与筛选
- `zotero-corpus-sync`：Zotero 身份匹配、同步与导入计划
- `social-science-paper-extraction`：论文证据和结构化抽取
- `quantitative-study-audit`：定量设计、模型与因果语言审计
- `research-knowledge-synthesis`：Finding、Claim、Concept、矩阵和综述
- `obsidian-research-kb`：Obsidian 渲染与结构检查
- `research-kb-evolution`：纠错、评测与版本晋升
- `policy-citation-knowledge-base`：政策引用领域兼容入口
- `runtime/`：确定性状态、增量、校验、幂等、报告与打包运行时

## 安装

要求 Python 3.10 或更高版本。本项目核心运行时仅使用 Python 标准库。

1. 克隆仓库并生成可安装的 Skill 目录：

   ```powershell
   git clone https://github.com/RC721/social-science-empirical-kb-skills.git
   cd social-science-empirical-kb-skills
   python runtime/research-kb.py --vault "D:\path\to\your-vault" package-skills --apply --output dist
   ```

2. 将 `dist/` 下的九个 Skill 文件夹复制到 Codex 的用户 Skill 目录：

   ```text
   C:\Users\<username>\.codex\skills\
   ```

3. 重新打开 Codex 任务，确认 `$social-science-empirical-kb` 可以被识别。

如果只使用当前开发仓库，也可直接调用 `runtime/research-kb.py`；运行时会在指定 Vault 的 `90_Codex工作区/` 下创建状态、配置、证据和报告目录。

## 最常用的方式：在 Codex 中调用

在提示词中明确写出 Skill 名称和目标。例如：

```text
使用 $social-science-empirical-kb，为“平台劳动者算法管理”建立 focused 模式的社会科学实证研究知识库。先生成检索协议和 Zotero 导入计划，不要直接写入 Zotero。
```

```text
使用 $social-science-paper-extraction 和 $quantitative-study-audit，处理 Zotero Collection 中新增且已有 PDF 的论文，每批 10 篇；生成 Evidence、结构化抽取和方法审计，并更新 Obsidian 文献笔记的机器管理区。
```

```text
使用 $research-knowledge-synthesis，基于已核验 Evidence 和 Literature Notes 更新论断、概念、比较矩阵和主题综述；单篇论断标为 preliminary，不把观察性相关写成因果关系。
```

政策引用项目可以使用兼容入口：

```text
使用 $policy-citation-knowledge-base，同步 Zotero 的“政策引用论文”Collection，只处理新增或上游已变化的条目。
```

## 命令行快速开始

以下示例假定当前目录为本仓库根目录。

```powershell
# 初始化 Vault 配置
python runtime/research-kb.py --vault "D:\path\to\vault" init --collection-key COLLECTION_KEY --domain general

# 先做不写入的全流程预演
python runtime/research-kb.py --vault "D:\path\to\vault" update --dry-run --batch-size 10

# 执行已允许自动运行的增量步骤
python runtime/research-kb.py --vault "D:\path\to\vault" update --apply --batch-size 10

# 检查结构、证据边界和异常
python runtime/research-kb.py --vault "D:\path\to\vault" audit --apply

# 运行黄金论文评测
python runtime/research-kb.py --vault "D:\path\to\vault" eval --apply
```

可用子命令：`init`、`discover`、`ingest`、`sync`、`migrate`、`extract`、`synthesize`、`render`、`audit`、`eval`、`update` 和 `package-skills`。多数写入命令支持 `--dry-run` 与 `--apply`；还可按 `--item-key`、`--collection-key`、`--run-id` 和 `--batch-size` 缩小处理范围。

## 推荐工作流

1. `discover` 形成检索协议、候选池、去重与筛选日志。
2. `ingest --plan` 只生成 Zotero 写入计划；人工确认后再 `ingest --apply`。
3. `sync` 比较 Zotero 版本、PDF 哈希和 manifest，建立增量任务队列。
4. `extract` 从 Metadata、Abstract 或 PDF 建立 Evidence 与 Study/Variable/Model/Finding Cards。
5. `quantitative-study-audit` 检查估计对象、识别策略、模型设定、稳健性及因果语言边界。
6. `synthesize` 生成或更新论断、概念、关系、比较矩阵与主题综述。
7. `render` 只更新 Obsidian 文档中的机器管理区，保留研究者笔记。
8. `audit` 和 `eval` 负责发布前验证；人工纠错进入演化账本，规则升级须经审核。

## 证据与安全边界

- Zotero 是身份、Metadata 与 PDF 的权威源。
- 原文证据只保存在 Evidence Artifact；Markdown 使用中文重述并标注原文位置。
- `metadata-only` 和 `abstract-only` 不越级推断全文方法、控制变量或详细局限。
- 语义相似只产生候选关系，不能自动成为正式知识关系。
- Zotero 批量写入、身份冲突、schema 迁移、第三方 Skill 升级和不可逆操作必须人工确认。
- 自动化只修改显式机器管理区，不覆盖 Obsidian 中的人工内容。

## 开发与验证

```powershell
python -m unittest discover -s tests -v
python runtime/research-kb.py --vault "D:\path\to\vault" package-skills --dry-run
```

`skill-development/` 是唯一开发源；发布副本应由 `package-skills` 生成，不应直接修改。
