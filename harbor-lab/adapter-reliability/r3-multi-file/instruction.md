# Task: Create Multiple Files

在当前工作目录 /app 中创建以下三个文件。

要求：

1. 创建所有必要的父目录。
2. 创建三个文件，路径必须完全一致。
3. 文件内容必须与下面给出的内容逐字一致。
4. 使用 UTF-8 编码。
5. 每个文件末尾保留一个 LF 换行符。
6. 不得遗漏任何文件。
7. 创建完成后重新读取三个文件，验证内容。
8. 不得修改 tests 目录中的任何文件。

## File 1

Path: /app/output/summary.txt

Content:

Project: R3 Multi-file Smoke Test
Status: complete
Files: 3

## File 2

Path: /app/output/data/records.csv

Content:

id,name,status
1,alpha,ready
2,beta,ready
3,gamma,ready

## File 3

Path: /app/output/config/settings.json

Content:

{
  "project": "R3",
  "version": 1,
  "enabled": true
}

完成后简要报告三个文件的创建结果。
