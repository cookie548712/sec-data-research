#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEC Financial Statement Data Sets 全自动爬取 + 下载 + 解压 + txt转csv
目标页: https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
XPath: /html/body/main/div[2]/div/div/div/div[1]/div/div[2]/div[4]/div/div/div/div/table/tbody/tr[1]/td[1]/a
流程: 提取全部季度zip链接 -> 下载 -> 按 "2026_Q2" 建文件夹 -> 自动解压 -> 自动把 *.txt(TSV) 转 *.csv(逗号分隔)

SEC 要求必须带 User-Agent (含联系邮箱) 否则 403
txt 实际是 TSV (tab分隔)，含 sub/pre/num/tag 四表，csv转换保持表头+正确引号转义
"""

import argparse
import csv
import os
import re
import time
import zipfile
import random
from pathlib import Path
from urllib.parse import urljoin

import requests
from lxml import html

# ============ 配置区 ============
BASE_URL = "https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets"
XPATH_FIRST = "/html/body/main/div[2]/div/div/div/div[1]/div/div[2]/div[4]/div/div/div/div/table/tbody/tr[1]/td[1]/a"
XPATH_ALL   = "/html/body/main/div[2]/div/div/div/div[1]/div/div[2]/div[4]/div/div/div/div/table/tbody/tr/td[1]/a"
XPATH_FALLBACK = '//table//tr/td[1]/a[contains(@href, ".zip")]'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SampleCompany contact@example.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Host": "www.sec.gov",
}

ROOT_DIR = Path(__file__).parent
DOWNLOAD_DIR = ROOT_DIR / "downloads"
DATA_DIR = ROOT_DIR / "data"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

LIMIT = None
OVERWRITE_ZIP = False
OVERWRITE_EXTRACT = False

# ---- txt转csv 配置 ----
AUTO_TXT_TO_CSV = True        # 解压后自动转csv
CSV_OVERWRITE = False         # 已存在csv是否覆盖
CSV_ENCODING_OUT = "utf-8-sig"  # utf-8-sig 让Excel直接中文不乱码，改 "utf-8" 可去掉BOM
KEEP_TXT = True               # 是否保留原txt
CSV_PROGRESS_EVERY = 500_000  # 大文件每N行打印进度（num.txt约360万行）


def fetch_page(url: str) -> str:
    print(f"[1] 请求列表页: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_links(page_html: str):
    tree = html.fromstring(page_html)
    nodes = tree.xpath(XPATH_ALL)
    if not nodes:
        print(f"[!] 精确XPath未命中，尝试备用XPath: {XPATH_FALLBACK}")
        nodes = tree.xpath(XPATH_FALLBACK)
    if not nodes:
        nodes = tree.xpath('//table//td[1]/a[contains(@href,".zip")]')
    results = []
    for a in nodes:
        href = a.get("href")
        text = (a.text_content() or "").strip()
        if not href:
            continue
        full_url = urljoin("https://www.sec.gov", href)
        quarter = ""
        if text:
            quarter = text.replace(" ", "_").replace("-", "_")
        else:
            m = re.search(r"(\d{4})q([1-4])", href, re.I)
            if m:
                quarter = f"{m.group(1)}_Q{m.group(2)}"
        quarter = re.sub(r"q(\d)", r"Q\1", quarter, flags=re.I)
        if not re.match(r"\d{4}_Q[1-4]", quarter):
            m = re.search(r"(\d{4})q([1-4])", href, re.I)
            if m:
                quarter = f"{m.group(1)}_Q{m.group(2)}"
            else:
                quarter = text or "unknown"
        results.append((quarter, full_url))
    first = tree.xpath(XPATH_FIRST)
    if first:
        print(f"[2] 验证用户XPath成功: {XPATH_FIRST} -> {first[0].get('href')}  文本={first[0].text_content().strip()}")
    else:
        print(f"[!] 用户指定的单行XPath未命中: {XPATH_FIRST}")
    seen = set()
    deduped = []
    for q, u in results:
        if u not in seen:
            seen.add(u)
            deduped.append((q, u))
    print(f"[2] 共解析到 {len(deduped)} 个季度包")
    for q, u in deduped[:5]:
        print(f"    - {q}: {u}")
    if len(deduped) > 5:
        print(f"    ... 还有 {len(deduped)-5} 个")
    return deduped


def download_zip(quarter: str, url: str) -> Path:
    zip_path = DOWNLOAD_DIR / f"{quarter}.zip"
    if zip_path.exists() and not OVERWRITE_ZIP and zip_path.stat().st_size > 0:
        print(f"[跳过] {quarter} 已存在: {zip_path.name}")
        return zip_path
    print(f"[下载] {quarter} <- {url}")
    time.sleep(random.uniform(0.5, 1.2))
    with requests.get(url, headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*64):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r      {quarter}: {downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB ({pct:.1f}%)", end="", flush=True)
        print(f"\r      {quarter}: 完成 {downloaded/1024/1024:.2f} MB -> {zip_path.name}      ")
    return zip_path


def extract_zip(quarter: str, zip_path: Path):
    folder_q = DATA_DIR / quarter
    if folder_q.exists() and any(folder_q.iterdir()) and not OVERWRITE_EXTRACT:
        print(f"[解压跳过] {quarter} 已解压: {folder_q}")
        return folder_q
    folder_q.mkdir(parents=True, exist_ok=True)
    print(f"[解压] {zip_path.name} -> {folder_q}/")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(folder_q)
            names = z.namelist()
            print(f"      包含 {len(names)} 个文件: {names[:4]}{'...' if len(names)>4 else ''}")
    except zipfile.BadZipFile as e:
        print(f"[错误] {quarter} zip损坏: {e}")
        zip_path.unlink(missing_ok=True)
        raise
    return folder_q


# ============ 新增：txt(TSV) -> csv ============
def convert_single_txt_to_csv(txt_path: Path, csv_path: Path = None, overwrite: bool = False) -> Path | None:
    """
    单个txt转csv：输入是SEC的TSV (tab分隔)，输出标准CSV (逗号分隔，带引号转义)
    流式处理，支持600MB/360万行大文件
    """
    if csv_path is None:
        csv_path = txt_path.with_suffix(".csv")
    if csv_path.exists() and not overwrite:
        print(f"  [CSV跳过] {csv_path.name} 已存在")
        return csv_path

    start = time.time()
    rows = 0
    # 统计输入大小
    in_size = txt_path.stat().st_size

    # 用 csv 模块正确处理引号/逗号/换行
    with open(txt_path, "r", encoding="utf-8", newline="", errors="replace") as fin, \
         open(csv_path, "w", encoding=CSV_ENCODING_OUT, newline="") as fout:
        reader = csv.reader(fin, delimiter="\t", quoting=csv.QUOTE_MINIMAL, doublequote=True)
        writer = csv.writer(fout, delimiter=",", quoting=csv.QUOTE_MINIMAL, quotechar='"', doublequote=True, lineterminator="\n")
        for row in reader:
            writer.writerow(row)
            rows += 1
            if rows % CSV_PROGRESS_EVERY == 0:
                print(f"    ... {txt_path.name}: 已处理 {rows:,} 行")

    elapsed = time.time() - start
    out_size = csv_path.stat().st_size
    print(f"  [CSV完成] {txt_path.name} ({in_size/1024/1024:.1f}MB, {rows:,}行) -> {csv_path.name} ({out_size/1024/1024:.1f}MB) 耗时{elapsed:.1f}s")
    if not KEEP_TXT:
        txt_path.unlink()
        print(f"    已删除原txt: {txt_path.name}")
    return csv_path


def convert_txts_to_csv(quarter_folder: Path, overwrite: bool = False) -> list[Path]:
    """
    转换一个季度文件夹下全部 *.txt -> *.csv
    返回生成的csv路径列表
    """
    if not quarter_folder.exists():
        print(f"[CSV] 文件夹不存在: {quarter_folder}")
        return []
    txt_files = sorted(quarter_folder.glob("*.txt"))
    if not txt_files:
        print(f"[CSV] {quarter_folder.name} 无txt文件，跳过")
        return []
    print(f"[CSV] 开始转换 {quarter_folder.name}: {len(txt_files)} 个txt -> csv")
    out = []
    for txt in txt_files:
        try:
            p = convert_single_txt_to_csv(txt, overwrite=overwrite)
            if p:
                out.append(p)
        except Exception as e:
            print(f"  [CSV失败] {txt.name}: {e}")
    print(f"[CSV] {quarter_folder.name} 转换完成: {len(out)}/{len(txt_files)}")
    return out


def convert_all_existing(overwrite: bool = False):
    """批量转换 data/ 下全部已有季度"""
    if not DATA_DIR.exists():
        print("[CSV] data目录不存在")
        return
    quarters = [p for p in DATA_DIR.iterdir() if p.is_dir()]
    if not quarters:
        print("[CSV] 无已解压季度")
        return
    print(f"[CSV] 批量转换全部 {len(quarters)} 个季度")
    for q in sorted(quarters):
        convert_txts_to_csv(q, overwrite=overwrite)


def main():
    parser = argparse.ArgumentParser(description="SEC Financial Statement 爬虫 + 自动txt转csv")
    parser.add_argument("--limit", type=int, default=None, help="只下最近N个季度，默认用脚本内LIMIT")
    parser.add_argument("--no-csv", action="store_true", help="关闭自动txt转csv")
    parser.add_argument("--csv-only", action="store_true", help="仅对已解压的data/*做txt->csv，不下载")
    parser.add_argument("--csv-overwrite", action="store_true", help="csv已存在时覆盖")
    parser.add_argument("--all", action="store_true", help="下载全部季度（覆盖LIMIT）")
    args = parser.parse_args()

    # csv-only 模式
    if args.csv_only:
        print("="*60)
        print("仅执行 txt -> csv 批量转换")
        print("="*60)
        convert_all_existing(overwrite=args.csv_overwrite or CSV_OVERWRITE)
        print("完成")
        return

    do_csv = not args.no_csv and AUTO_TXT_TO_CSV
    csv_overwrite = args.csv_overwrite or CSV_OVERWRITE

    print("="*60)
    print("SEC Financial Statement Data Sets 爬虫")
    print(f"目标: {BASE_URL}")
    print(f"XPath(首行): {XPATH_FIRST}")
    print(f"XPath(全部): {XPATH_ALL}")
    print(f"自动txt转csv: {do_csv}  (CSV_OVERWRITE={csv_overwrite}, 编码={CSV_ENCODING_OUT})")
    print("="*60)

    page = fetch_page(BASE_URL)
    items = parse_links(page)

    # 限制处理
    limit = None if args.all else (args.limit if args.limit is not None else LIMIT)
    if limit:
        items = items[:limit]
        print(f"[限制] 仅处理前 {limit} 个季度")

    if not items:
        print("[失败] 未解析到任何下载链接")
        return

    for quarter, url in items:
        try:
            zp = download_zip(quarter, url)
            folder = extract_zip(quarter, zp)
            if do_csv:
                convert_txts_to_csv(folder, overwrite=csv_overwrite)
        except Exception as e:
            print(f"[异常] {quarter} 处理失败: {e}")
            continue

    # 额外：把历史已存在但未转csv的季度也补转一次
    if do_csv:
        print("\n[收尾] 检查历史季度是否漏转csv...")
        for quarter, _ in items:
            folder = DATA_DIR / quarter
            # 如果该季度有txt但无对应csv则补转
            txts = list(folder.glob("*.txt"))
            csvs = list(folder.glob("*.csv"))
            if txts and len(csvs) < len(txts):
                convert_txts_to_csv(folder, overwrite=csv_overwrite)

    print("\n全部完成!")
    print(f"  zip目录: {DOWNLOAD_DIR}")
    print(f"  解压目录: {DATA_DIR}")
    for p in sorted(DATA_DIR.iterdir())[:5]:
        if not p.is_dir():
            continue
        txts = list(p.glob("*.txt"))
        csvs = list(p.glob("*.csv"))
        print(f"    data/{p.name}/  txt:{len(txts)} csv:{len(csvs)}  -> {', '.join(c.name for c in csvs[:3])}")


if __name__ == "__main__":
    main()
