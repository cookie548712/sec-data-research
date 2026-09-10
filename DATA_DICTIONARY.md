# SEC Financial Statement Data Sets — CSV 数据字典

> 来源：`https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets`  
> 官方文档：`data/{季度}/readme.htm` · 提取自 XBRL 原始提交 · 2009-Q1 至今季度更新  
> 本地已转：`data/2026_Q2/*.txt(TSV) → *.csv(UTF-8-SIG, 逗号, 首行小写)` · 解压后自动转换 `sec_crawler.py`

---

## 0. 总览

| 数据集 | 文件 | 本地大小(2026_Q2实测) | 1行= | 主键(Key `*`) | 作用一句话 |
|---|---|---|---|---|---|
| **SUB** | `sub.csv` / `sub.txt` | 2.3 MB · 36列 | 1次XBRL提交 | `adsh*` | 目录/封面：公司是谁、哪份报告、哪一天提交 |
| **NUM** | `num.csv` / `num.txt` | 601 MB · 3,608,713行 · 10列 | 1个数值事实 | `adsh+tag+version+ddate+qtrs+uom+segments+coreg*` | 核心：所有财报上的钱 |
| **TAG** | `tag.csv` / `tag.txt` | 19 MB · 9列 | 1个XBRL标签 | `tag+version*` | 字典：科目叫什么、什么类型、借贷方向 |
| **PRE** | `pre.csv` / `pre.txt` | 96 MB · 10列 | 财报上1行列示 | `adsh+report+line*` | 版式：这个数在第几张表第几行、显示什么文字 |

**文件格式**：官方 `Tab \t` 分隔、`utf-8`、`LF` 换行、首行列名；本项目自动转 `CSV` 时首行不变、内容用 `csv.QUOTE_MINIMAL` 处理逗号/引号/换行，编码 `utf-8-sig` (Excel不乱码，改 `sec_crawler.py:CSV_ENCODING_OUT="utf-8"` 可去BOM)。

**关联关系**：

```
SUB --1:N-- NUM --N:1-- TAG
 |                \
 |                 N:1 -- PRE  (1个NUM可对应多行PRE，如 NetIncome 同时在 IS和CF)
 SUB --1:N-- PRE
```

* `NUM.adsh = SUB.adsh` 查提交信息
* `NUM.tag+NUM.version = TAG.tag+TAG.version` 查科目定义
* `PRE.adsh+PRE.tag+PRE.version = NUM.adsh+NUM.tag+NUM.version` 查列示位置

> EDGAR 原件地址：`https://www.sec.gov/Archives/edgar/data/{cik}/{adsh去-}/{instance}`  
> SQL示例：`select 'https://www.sec.gov/Archives/edgar/data/'||ltrim(str(cik,10))||'/'||replace(adsh,'-','')||'/'||instance as url from sub`

---

## 1. `sub.csv` — Submissions 提交目录表

> 预览头（36列）：`adsh,cik,name,sic,countryba,stprba,cityba,zipba,bas1,bas2,baph,countryma,stprma,cityma,zipma,mas1,mas2,countryinc,stprinc,ein,former,changed,afs,wksi,fye,form,period,fy,fp,filed,accepted,prevrpt,detail,instance,nciks,aciks`

**主键**：`adsh` (20位 `nnnnnnnnnn-nn-nnnnnn`，如 `0000001961-26-000014`) · 来源分 `EDGAR`(提交头) / `XBRL`(申报内容)

| 列名 | 中文 | 官方描述 | 来源/格式 | 最大 | 可空 | 键 | 示例 |
|---|---|---|---|---|---|---|---|
| **adsh*** | 受理号PK | 20位EDGAR受理号，SEC分配 | EDGAR `ALPHANUMERIC` | 20 | No | * | `0000001961-26-000014` |
| **cik** | 公司CIK | 10位SEC注册人编号 | EDGAR `NUMERIC` | 10 | No |  | `1961` |
| **name** | 法定全称 | EDGAR记录的法人名(提交日) | EDGAR | 150 | No |  | `GEMAXEL INC` |
| **sic** | 行业码 | SEC四位SIC | EDGAR `NUMERIC` | 4 | Yes |  | `7372` |
| **countryba** | 营业地址-国家 | ISO 3166-1 | EDGAR | 2 | Yes |  | `US` |
| **stprba** | 营业地址-州 | 仅US/CA有值 | EDGAR | 2 | Yes |  | `FL` |
| **cityba** | 营业地址-市 |  | EDGAR | 30 | Yes |  | `MIAMI BEACH` |
| **zipba** | 营业地址-邮编 |  | EDGAR | 10 | Yes |  | `33140` |
| **bas1** | 营业地址-街1 |  | EDGAR | 40 | Yes |  | `4775 COLLINS AVE` |
| **bas2** | 营业地址-街2 |  | EDGAR | 40 | Yes |  |  |
| **baph** | 营业电话 |  | EDGAR | 20 | Yes |  | `917-270-1187` |
| **countryma** | 邮寄地址-国家 |  | EDGAR | 2 | Yes |  | `US` |
| **stprma** | 邮寄地址-州 |  | EDGAR | 2 | Yes |  | `FL` |
| **cityma** | 邮寄地址-市 |  | EDGAR | 30 | Yes |  | `MIAMI BEACH` |
| **zipma** | 邮寄地址-邮编 |  | EDGAR | 10 | Yes |  | `33140` |
| **mas1** | 邮寄地址-街1 |  | EDGAR | 40 | Yes |  | `4775 COLLINS AVE` |
| **mas2** | 邮寄地址-街2 |  | EDGAR | 40 | Yes |  |  |
| **countryinc** | 注册地-国家 | Incorporation | EDGAR | 3 | Yes |  | `US` |
| **stprinc** | 注册地-州 |  | EDGAR | 2 | Yes |  | `DE` |
| **ein** | 美国税号 | 9位IRS Employer ID | EDGAR `NUMERIC` | 10 | Yes |  | `221848316` |
| **former** | 曾用名 | 最近一次曾用名 | EDGAR | 150 | Yes |  | `WORLDS INC` |
| **changed** | 更名日 | `yyyymmdd` | EDGAR | 8 | Yes |  | `20111115` |
| **afs** | 申报人规模 | `1-LAF大型加速 2-ACC加速 3-SRA小加速 4-NON非加速 5-SML小公司` | XBRL | 5 | Yes |  | `4-NON` |
| **wksi** | 知名成熟发行人 | `1是 0否` | XBRL `BOOLEAN` | 1 | No |  | `0` |
| **fye** | 财年截止 | 月日 `mmdd` 取整到月末 | XBRL | 4 | Yes |  | `1231` |
| **form** | 提交类型 | `10-K 10-Q 20-F 40-F 8-K` 等 | EDGAR | 10 | No |  | `10-Q` |
| **period** | 资产负债表日 | `yyyymmdd` 取整到月末 | XBRL `DATE` | 8 | No |  | `20250331` |
| **fy** | 财年焦点 | `yyyy` | XBRL `YEAR` | 4 | Yes |  | `2025` |
| **fp** | 财季焦点 | `FY/Q1/Q2/Q3/Q4` | XBRL | 2 | Yes |  | `Q1` |
| **filed** | 提交日 | 向SEC提交日 `yyyymmdd` | EDGAR `DATE` | 8 | No |  | `20260605` |
| **accepted** | 接受时间 | `yyyy-mm-dd hh:mm:ss` | EDGAR `DATETIME` | 19 | No |  | `2026-06-04 17:44:00.0` |
| **prevrpt** | 是否被修订 | `1=旧版已被后续amend` | EDGAR `BOOLEAN` | 1 | No |  | `0` |
| **detail** | 脚注明细分 | `1=脚注已逐金额打标签` | XBRL `BOOLEAN` | 1 | No |  | `1` |
| **instance** | 实例文件名 | 常以ticker开头 `abcd-yyyymmdd.xml` | EDGAR | 40 | No |  | `wddd10q125_htm.xml` |
| **nciks** | 合并含几家CIK |  | EDGAR `NUMERIC` | 4 | No |  | `1` |
| **aciks** | 其他联合CIK | 空格分隔，`nciks=1`时NULL，超长截断 | EDGAR | 120 | Yes |  |  |

> 注意：EDGAR字段取“提交日当时”的分配，不一定是最新；`adsh` 去掉 `-` 即文件夹名。

---

## 2. `num.csv` — Numbers 数值事实表

> 预览头（10列）：`adsh,tag,version,ddate,qtrs,uom,segments,coreg,value,footnote`  
> 实测 `2026_Q2: adsh,tag,version,ddate,qtrs,uom,segments,coreg,value,footnote` 第一行 `0000001961-26-000014,AccountsPayableCurrent,us-gaap/2025,20241231,0,USD,,,809928.0000,`

**复合主键**：`adsh + tag + version + ddate + qtrs + uom + segments + coreg` (8列均 `*`，`value/footnote` 非键)

| 列名 | 中文 | 官方描述 | 格式 | 最大 | 可空 | 键 | 要点 |
|---|---|---|---|---|---|---|---|
| **adsh*** | 受理号FK | 关联 `SUB.adsh` | ALPHANUMERIC | 20 | No | * |  |
| **tag*** | 标签名 | 准则科目名 `Revenues`/`Assets` | ALPHANUMERIC | 256 | No | * | 区分大小写 |
| **version*** | 准则版本 | 标准=`us-gaap/2025` 自定义=`adsh` | ALPHANUMERIC | 20 | No | * |  |
| **ddate*** | 期间终点 | 取整到月末 `yyyymmdd` | DATE | 8 | No | * | `20241231` |
| **qtrs*** | 涵盖季度数 | `0=时点数(资产负债) 1=单季 2=半年 4=全年` 四舍五入 | NUMERIC | 8 | No | * | **关键**：查BS用 `0`，IS用 `1或4` |
| **uom*** | 计量单位 | `USD` `USD per share` `shares` 等 | ALPHANUMERIC | 20 | No | * |  |
| **segments*** | 维度拆分 | `轴+成员` (Axis/Member)，空=合并 | ALPHANUMERIC | 1024 | Yes | * | 合并分析请过滤 `segments IS NULL` |
| **coreg*** | 联合注册人 | 指定子主体/担保人，空=合并主体 | ALPHANUMERIC | 256 | Yes | * | 合并分析请过滤空 |
| **value** | 金额 | 未缩放、保留4位小数 `NUMERIC(28,4)` | NUMERIC | 16 | Yes |  | `809928.0000` 非千分位，已是原值 |
| **footnote** | 脚注上标文本 | 报表页脚注截断512字，无则空 | ALPHANUMERIC | 512 | Yes |  |  |

**常见坑**：`value` 正负需结合 `TAG.crdr/iord`；`qtrs=0` 的 `value` 是快照，`qtrs=1/4` 是期间累计；`segments` 非空为分部/产品拆分，勿与合并混算。

---

## 3. `tag.csv` — Tags 科目字典表

> 预览头（9列）：`tag,version,custom,abstract,datatype,iord,crdr,tlabel,doc`  
> 第一行 `AccountsAndNotesReceivableNet,us-gaap/2024,0,0,monetary,I,D,Accounts and Financing Receivable...`

**主键**：`tag + version` (`*`)

| 列名 | 中文 | 官方描述 | 类型 | 最大 | 可空 | 键 | 枚举/示例 |
|---|---|---|---|---|---|---|---|
| **tag*** | 标签名 | 唯一标识 | ALPHANUMERIC | 256 | No | * | `AccountsPayableCurrent` |
| **version*** | 版本 | 标准=taxonomy名 自定义=adsh | ALPHANUMERIC | 20 | No | * | `us-gaap/2025` |
| **custom** | 是否自定义 | `1自定义 0标准` (冗余version判断) | BOOLEAN `1/0` | 1 | No |  | `0` |
| **abstract** | 是否抽象标题 | `1=标题不存数` | BOOLEAN | 1 | No |  | `0` |
| **datatype** | 数据类型 | `abstract=1时NULL` | ALPHANUMERIC | 20 | Yes |  | `monetary/shares/perShare/string` |
| **iord** | 时点/期间 | `abstract=1时NULL` | ALPHANUMERIC `I/D` | 1 | No |  | `I=Instant时点 D=Duration期间` |
| **crdr** | 自然借贷 | 仅`monetary`有值 | ALPHANUMERIC `C/D` | 1 | Yes |  | `D借 C贷` 资产多为D |
| **tlabel** | 标签标题 | 标准取taxonomy，自定义取公司 | ALPHANUMERIC | 512 | Yes |  | `Accounts Payable, Current` |
| **doc** | 详细定义 | 长文本，无则NULL | ALPHANUMERIC | — | Yes |  | 准则原文 |

> 关联：`NUM.tag+NUM.version → TAG.tag+TAG.version` 即可得 `tlabel/doc` 中文语义、借贷、时点/期间。

---

## 4. `pre.csv` — Presentation 报表列示表

> 预览头（10列）：`adsh,report,line,stmt,inpth,rfile,tag,version,plabel,negating`  
> 第一行 `0000001961-26-000014,2,2,UN,0,H,CashAndCashEquivalentsAtCarryingValue,us-gaap/2025,Cash and cash equivalents,0`

**主键**：`adsh + report + line` (`*`) · **注意**：1个 `NUM` 可对应多行 `PRE` (如 `NetIncome` 同时在 `IS` 和 `CF`)

| 列名 | 中文 | 官方描述 | 格式 | 最大 | 可空 | 键 | 枚举 |
|---|---|---|---|---|---|---|---|
| **adsh*** | 受理号FK | 关联 `SUB/NUM` | ALPHANUMERIC | 20 | No | * |  |
| **report*** | 报告分组号 | 对应EDGAR `R` 文件序号，对应 `stmt` | NUMERIC | 6 | No | * | `2` |
| **line*** | 行号 | 同一report内顺序，决定显示顺序 | NUMERIC | 6 | No | * | `2` |
| **stmt** | 报表类型 |  | ALPHANUMERIC | 2 | No |  | `BS资产负债 IS利润 CF现金流 EQ权益 CI综合收益 SI投资表 UN未分类` |
| **inpth** | 括号内披露 | `1=Parenthetical` 例 `应收(坏账备抵$200) $700` | BOOLEAN | 1 | No |  | `0/1` |
| **rfile** | 渲染文件 | EDGAR渲染类型 | ALPHANUMERIC | 1 | No |  | `H=.htm X=.xml` |
| **tag** | 标签 | 行对应标签 | ALPHANUMERIC | 256 | No |  |  |
| **version** | 版本 | 同TAG | ALPHANUMERIC | 20 | No |  |  |
| **plabel** | 显示标签 | 行显示文字 Preferred Label | ALPHANUMERIC | 512 | No |  | `Cash and cash equivalents` |
| **negating** | 是否取反 | `1=显示时取反` | BOOLEAN | 1 | No |  | `0/1` |

**用途**：按 `report,line` 排序即可还原财报版式；`plabel` 是财报上实际写的文字，`tag.tlabel` 是准则字典标题，两者可能不同。

---

## 5. 快速开始

### pandas

```python
import pandas as pd
base = "data/2026_Q2"
sub = pd.read_csv(f"{base}/sub.csv", dtype=str, keep_default_na=False)
num = pd.read_csv(f"{base}/num.csv", dtype=str, keep_default_na=False)
tag = pd.read_csv(f"{base}/tag.csv", dtype=str, keep_default_na=False)
pre = pd.read_csv(f"{base}/pre.csv", dtype=str, keep_default_na=False)

# 1) 查某公司(如AAPL cik=320193)最新提交
cik = "320193"  # Apple = 320193, 可从 sub.name 搜
adsh = sub[sub.cik == cik].sort_values("period", ascending=False).iloc[0].adsh

# 2) 查该提交的营收(单季) — qtrs=1
# 需先过滤合并：segments=="" and coreg==""
rev = num[(num.adsh==adsh) & (num.tag=="Revenues") & (num.qtrs=="1") & (num.segments=="")][["ddate","value","uom","segments"]]
print(rev.head())

# 3) 关联字典看定义
num.merge(tag, on=["tag","version"], how="left")[["tag","tlabel","datatype","iord","crdr","value"]].head()

# 4) 还原利润表版式
pre[(pre.adsh==adsh) & (pre.stmt=="IS")].sort_values(["report","line"])[["line","plabel","tag","version"]].head(10)
```

### SQL (DuckDB/SQLite)

```sql
-- 生成EDGAR原文链接
SELECT name, form, period,
  'https://www.sec.gov/Archives/edgar/data/'||ltrim(str(cik,10))||'/'||replace(adsh,'-','')||'/'||instance AS url
FROM sub ORDER BY period DESC;

-- 合并口径的资产负债表 Total Assets (时点数 qtrs=0)
SELECT s.name, n.ddate, n.value
FROM num n JOIN sub s ON n.adsh=s.adsh
JOIN tag t ON n.tag=t.tag AND n.version=t.version
WHERE n.tag='Assets' AND n.qtrs='0' AND n.segments='' AND n.coreg IS NULL
ORDER BY n.ddate DESC LIMIT 10;
```

### 常见科目 tag 速查

| 科目 | 常用 tag |
|---|---|
| 资产总额 | `Assets` |
| 现金 | `CashAndCashEquivalentsAtCarryingValue` |
| 营收 | `Revenues` / `RevenueFromContractWithCustomerExcludingAssessedTax` / `SalesRevenueNet` |
| 净利润 | `NetIncomeLoss` |
| 每股收益 | `EarningsPerShareBasic` / `EarningsPerShareDiluted` |
| 经营现金流 | `NetCashProvidedByUsedInOperatingActivities` |

> 不同公司/年份 `version(us-gaap/2024 vs 2025)` 可能不同，查询时建议 `tag` 模糊或关联 `tag` 表确认。

---

## 6. 注意事项

1. **As Filed 未修正**：含公司填报错误、冗余、修订前数据，`prevrpt=1` 表示旧版已被amend，官方季度末后提交的会进下季度包。
2. **仅主表**：范围限 `BS/IS/CF/EQ/CI` 五大主表 + 其页脚注，不含附注全文。
3. **单位与缩放**：`value` 已是未缩放原值，注意 `uom` (`USD` vs `USD per share`)；`tag.datatype=monetary` 的借贷 `crdr` 仅作语义参考。
4. **时点 vs 期间**：`NUM.qtrs=0 + ddate` 查快照；`qtrs>0` 查期间累计，务必带 `ddate+qtrs` 联合过滤。
5. **分部数据**：`segments/coreg` 非空为拆分/子公司，合并分析必须 `segments="" AND coreg=""`。

---

*本文档由 `sec_crawler.py` 自动生成校验，字段定义以 `data/{季度}/readme.htm Figure 2-5` 为准。本地示例季度：`2026_Q2` (sub 2.3MB, num 601MB 360万行, tag 19MB, pre 96MB)。*
