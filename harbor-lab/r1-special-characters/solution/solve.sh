#!/bin/bash
set -eu

cat > /app/special.txt <<'CONTENT'
第一行：你好，DSH！
第二行：双引号 "你好" 与单引号 '你好'
第三行：反斜杠 \ 和美元符号 $HOME
第四行：Emoji：🐳 🚀
CONTENT
