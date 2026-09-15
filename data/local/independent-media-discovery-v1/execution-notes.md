# 执行记录

1. `python data/local/independent-media-discovery-v1/fetch_public.py`：3 次 robots GET、6 次文章 GET，全部 HTTP 200。没有重试或额外服务正文读取。
2. 初次 `python data/local/independent-media-discovery-v1/extract.py`：d01 完成，d02 的全文覆盖断言发现代码把 HTML 注释当正文加入。修正为跳过 `bs4.Comment`；来源响应完整保留，d01 产物未改动。
3. `python data/local/independent-media-discovery-v1/extract.py d02 d03 d04 d05 d06`：继续离线提取未完成的条目。提取完成后仍会逐篇通读全文，并验证每条精确引文。
4. `python data/local/independent-media-discovery-v1/analyze.py`：全文通读后保存逐篇助手分析、61处精确引文、五篇正文的阅读覆盖、有限范围去重及出处sidecar。结果为5篇、25,504字符、286块。
5. `python data/local/independent-media-discovery-v1/validate.py`：独立从原始响应重查DOM覆盖与JSON路径，核对全部请求和搜索上限、引用偏移、文件hash，生成 `validation.json` 与 `manifest.json`。不访问网络。

最初控制台通过系统默认编码显示中文时出现乱码；原始 HTML 经严格 UTF-8 解码正常。后续脚本显式使用 UTF-8 输出；没有“修正”来源文字或重编码原始响应。

Metaso 成功搜索响应共 6 个，各返回 `credits: 3`，合计已报告 18 credits。两次“未找到相关数据”响应不带计费字段；其费用未知。credits 到货币的换算及账户扣款未知。不调用 Metaso reader 或外部 LLM。
