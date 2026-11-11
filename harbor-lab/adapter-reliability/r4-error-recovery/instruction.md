# Task: Recover from a Transient Tool Failure

在当前工作环境中完成一次故障恢复任务。

## Task Requirements

1. 执行环境中预装的命令：

   /usr/local/bin/r4-operation

2. 第一次执行会产生一次预期的临时故障。
   仔细检查工具返回的错误信息和退出状态。

3. 分析失败原因，并进行一次合理的重试。

4. 重试成功后，不得再次调用该命令。

5. 重新读取以下两个文件：

   /app/output/result.txt
   /app/output/attempts.log

6. 验证最终结果和调用记录。

## Constraints

- 不得修改或替换 r4-operation。
- 不得修改 /tmp/r4-attempt-count。
- 不得手动创建或修改 result.txt。
- 不得手动创建或修改 attempts.log。
- 不得修改 tests 目录中的任何文件。
- 不得通过其他方式绕过故障注入机制。
- 最多调用 r4-operation 两次。

## Expected Result

result.txt must contain exactly:

Recovered after one retry

The attempts.log must contain exactly two records:

attempt=1 status=transient_failure
attempt=2 status=success

Both files must end with exactly one LF newline.

完成后简要报告故障原因、恢复过程和验证结果。
