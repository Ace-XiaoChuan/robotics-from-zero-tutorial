# 用 bash 执行时只影响子 shell；用 source 加载时影响当前 shell。
# 只设置本课专用变量，不修改 PATH、Python 环境或 ROS 环境。
export S0_LESSON_LABEL="loaded-from-script"
printf '脚本内 S0_LESSON_LABEL=%s\n' "$S0_LESSON_LABEL"
