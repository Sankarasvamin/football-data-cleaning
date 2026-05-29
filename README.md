# CSV Clean

本目录保存足球转会数据清洗与数据库导入准备工作。

## 目录结构

- `er.py`：用于辅助整理数据结构和实体关系的脚本。
- `data_structure_table.md`：字段结构说明文档。
- `data_structure_table.csv`：字段结构表格版本。
- `sql_ready/`：已清洗并可用于 MySQL 导入的小规模结构化数据、建表 SQL 和导入说明。

## 数据管理原则

原始 CSV 数据体积较大，其中部分文件超过 GitHub 单文件限制，不纳入 Git 版本管理。仓库中保留的是可复现清洗结果、SQL 结构、字段说明和小规模导入数据。

如需重新处理完整原始数据，请将原始 CSV 文件放回本目录，再根据 `sql_ready/README.md` 中的流程执行清洗与导入。

## 推荐使用顺序

1. 阅读 `data_structure_table.md` 理解原始字段。
2. 查看 `sql_ready/cleaned_tables_schema.md` 理解清洗后的表结构。
3. 使用 `sql_ready/mysql_schema.sql` 建表。
4. 使用 `sql_ready/mysql_load_data.sql` 导入 `sql_ready/` 中的 CSV 文件。
