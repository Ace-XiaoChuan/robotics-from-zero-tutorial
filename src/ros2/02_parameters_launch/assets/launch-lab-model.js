/* 时间模型与画面分离。所有时刻为教学假设；t 是模型秒，播放器倍速不改变事件关系。 */
(() => {
  "use strict";
  const chapters = {
    build: {
      number: "00",
      kind: "BUILD",
      stage: "BUILD & RUN",
      title: "改了源码，<br>运行的程序就变了吗？",
      duration: 10,
      description:
        "源码、安装结果、终端环境和运行进程是四件事。比较完整流程、漏构建和漏加载环境的结果。",
      label: "构建 → 加载环境 → 启动",
      context: "ros2_comm_demo",
      steps: [
        [0, "修改源码", "用 v1 / v2 标记安装程序的新旧，仅作示意。"],
        [
          2,
          "构建并安装，再加载环境",
          "build 更新安装结果；source 让当前终端找到它。",
        ],
        [
          6,
          "启动安装的程序",
          "command_node 是程序名，创建的节点却叫 command。",
        ],
      ],
      takeaway:
        "<strong>构建更新程序，source 更新当前终端的查找环境。</strong>只修改源码、只打开新终端，都不会自动完成构建。",
      next: "接下来：名称怎样展开",
    },
    names: {
      number: "01",
      kind: "NAMES",
      stage: "NAME RESOLUTION",
      title: "看起来同名，<br>为什么连不上？",
      duration: 9,
      description:
        "先解析节点名和话题名，再看发布端与订阅端是否落在同一个完整名称上。",
      label: "相对名 → 命名空间 → 重映射 → 名称匹配",
      context: "namespace / remapping",
      steps: [
        [
          0,
          "先区分节点名与接口名",
          "重命名节点，不会给普通相对话题加上节点名。",
        ],
        [
          2,
          "把话题名展开并重映射",
          "相对名受命名空间影响；绝对名从根路径开始。",
        ],
        [5, "比较两端的完整名称", "此图假设类型和 QoS 兼容，只观察名称匹配。"],
      ],
      takeaway:
        "<strong>namespace 与 remapping 改的是 ROS 名称。</strong>另例 robot_pose 位置消息里的 frame_id 仍是 map，不会自动添加机器人前缀或进行 TF 变换。",
      next: "接下来：参数何时改变行为",
    },
    parameters: {
      number: "02",
      kind: "PARAMETER",
      stage: "PARAMETER → TIMER",
      title: "参数值变了，<br>定时器就变了吗？",
      duration: 10,
      description:
        "先在构造时读取周期并创建定时器，再尝试运行中改参。脉冲间隔对应模型里的理想发布周期。",
      label: "读取启动参数 → 创建定时器 → 尝试运行中更新",
      context: "publish_period_s",
      steps: [
        [0, "启动配置进入节点", "源码默认周期 0.2 s；本例允许配置 ≥ 0.001 s。"],
        [
          2,
          "按读取值创建定时器",
          "周期 T 对应目标频率 1/T；实际调度可能有误差。",
        ],
        [
          4,
          "运行中尝试修改",
          "现有实现 read_only=true；两个可写模式是教学对照。",
        ],
      ],
      takeaway:
        "<strong>参数存储值和正在工作的对象要分别观察。</strong>现有电量节点运行中拒绝改参；换启动值并重启后才会重建定时器。",
      next: "接下来：launch 把配置放到一起",
    },
    launch: {
      number: "03",
      kind: "LAUNCH",
      stage: "LAUNCH RECIPE",
      title: "一份启动配方，<br>组织一组进程。",
      duration: 9,
      description:
        "以现有 launch.py 为例：命名空间传给四个节点，目标参数只传给客户端，还可按条件省略客户端。",
      label: "启动描述 → 求值启动参数 → 创建节点进程",
      context: "launch.py",
      steps: [
        [
          0,
          "读取启动描述与实参",
          "LaunchConfiguration 在 launch 上下文里取得参数值。",
        ],
        [
          2,
          "给各个 Node 分配配置",
          "namespace、parameters 和 condition 各有自己的作用。",
        ],
        [
          4,
          "按条件创建进程",
          "这份配置没有声明业务就绪依赖，不能靠列表顺序推断。",
        ],
      ],
      takeaway:
        "<strong>launch 保存“启动谁、带什么配置”。</strong>进程已经启动，还要另外检查服务注册、数据有效性和任务状态。",
      next: "接下来：从启动到真正就绪",
    },
    readiness: {
      number: "04",
      kind: "READINESS",
      stage: "STARTED ≠ READY",
      title: "进程启动之后，<br>还在等什么？",
      duration: 10,
      description:
        "客户端先启动：每 0.2 s 检查服务与动作端，再查询状态。有效且空闲时才发送一次运动目标。",
      label: "端点就绪 → 有效且空闲 → 只发送一次目标",
      context: "command_node.cpp",
      steps: [
        [
          0,
          "等 Service 和 Action 就绪",
          "服务端进程存在，不代表接口已经注册。",
        ],
        [
          2,
          "异步查询缓存状态",
          "响应需 valid=true 且 has_task=false；查询可重试。",
        ],
        [
          4.15,
          "发出目标后等待结果",
          "目标不自动重发；结果超时只尝试取消并报告未确认。",
        ],
      ],
      takeaway:
        "<strong>就绪等待可以重试，运动请求发送一次。</strong>固定睡眠不能替代状态检查；等待结果超时也不能当成任务已经停止。",
      next: "回到开头：重新梳理启动过程",
    },
  };
  const defaults = () => ({
    buildCase: "fresh",
    namespace: "arm_a",
    rename: true,
    absolute: false,
    remap: true,
    matchSubscriber: false,
    period: 0.2,
    paramMode: "readonly",
    launchNamespace: "lesson1",
    startCommand: true,
    targetX: 1,
    readyCase: "normal",
  });
  const path = (namespace, name) =>
    "/" + [namespace, name].filter(Boolean).join("/");
  function names(o) {
    const source = o.absolute ? "/battery_level" : "battery_level";
    const original = source.startsWith("/")
      ? source
      : path(o.namespace, source);
    const ruleFrom = path(o.namespace, "battery_level");
    const ruleTo = path(o.namespace, "battery_percent");
    const remapped = o.remap && original === ruleFrom;
    const published = remapped ? ruleTo : original;
    const subscribed = o.matchSubscriber ? published : "/battery_level";
    return {
      source,
      original,
      ruleFrom,
      ruleTo,
      remapped,
      published,
      subscribed,
      matched: published === subscribed,
      node: path(o.namespace, o.rename ? "battery_monitor" : "battery_node"),
      frame: "map", // 另例 robot_pose.header.frame_id；电量 Int32 没有此字段。
    };
  }
  function duration(chapter, o) {
    return chapter === "readiness"
      ? o.readyCase === "never"
        ? 32
        : o.readyCase === "result_timeout"
          ? 26
          : 10
      : chapters[chapter].duration;
  }
  function parameterSample(t, o) {
    const valid = Number.isFinite(o.period) && o.period >= 0.001;
    const attempted = t >= 4,
      applied = t >= 4.5;
    const requested = o.period === 0.5 ? 0.2 : 0.5;
    const writable = o.paramMode !== "readonly";
    const stored = applied && writable ? requested : o.period;
    const timer =
      applied && o.paramMode === "reconfigure" ? requested : o.period;
    const pulses = [];
    if (valid && t >= 2) {
      const end = applied && o.paramMode === "reconfigure" ? 4.5 : t;
      for (let k = 1; k <= Math.floor((end - 2) / o.period + 1e-8); k++)
        pulses.push(Number((2 + k * o.period).toFixed(6)));
      if (applied && o.paramMode === "reconfigure") {
        for (let k = 1; k <= Math.floor((t - 4.5) / requested + 1e-8); k++)
          pulses.push(Number((4.5 + k * requested).toFixed(6)));
      }
    }
    return {
      valid,
      requested,
      stored,
      timer,
      pulses,
      started: valid && t >= 2,
      attempted: valid && attempted,
      applied: valid && applied,
      accepted: valid && applied && writable,
      mode: o.paramMode,
      otherNodePeriod: 0.2,
    };
  }

  function readinessSample(t, o) {
    const mode = o.readyCase,
      endpointAt = mode === "never" ? Infinity : 2;
    const stateAt = 4,
      busyUntil = mode === "busy" ? 5 : 0;
    const requests = [];
    let missingUsed = false,
      blockedUntil = 0,
      goalAt = null;
    for (let tick = 0; tick <= 151; tick++) {
      const at = Number((tick * 0.2).toFixed(6));
      if (at < endpointAt || at < blockedUntil - 1e-7) continue;
      if (mode === "query_timeout" && !missingUsed) {
        requests.push({
          at,
          responseAt: null,
          clearedAt: at + 2.2,
          valid: false,
          busy: false,
        });
        blockedUntil = at + 2.4;
        missingUsed = true;
        continue;
      }
      const valid = at + 0.05 >= stateAt,
        busy = at + 0.05 < busyUntil;
      const responseAt = Number((at + 0.15).toFixed(6));
      requests.push({ at, responseAt, clearedAt: null, valid, busy });
      if (valid && !busy) {
        goalAt = responseAt;
        break;
      }
    }
    const visible = requests.filter((q) => q.at <= t);
    const latest = visible.at(-1) ?? null;
    const responses = visible.filter(
      (q) => q.responseAt !== null && q.responseAt <= t,
    );
    const response = responses.at(-1) ?? null;
    const sent = goalAt !== null && t >= goalAt;
    const accepted = sent && t >= goalAt + 0.25;
    const done = mode !== "result_timeout" && accepted && t >= goalAt + 2.35;
    // 定时器每 0.2 s 检查，条件是 > timeout，所以不在恰好 30.0 s / 20.0 s 触发。
    const startupTimeoutAt = 30.2;
    const resultTimeoutAt =
      goalAt === null
        ? Infinity
        : Number(
            ((Math.floor((goalAt + 20) / 0.2 + 1e-8) + 1) * 0.2).toFixed(6),
          );
    const startupTimedOut = !sent && t >= startupTimeoutAt;
    const resultTimedOut =
      mode === "result_timeout" && sent && t >= resultTimeoutAt;
    const pending =
      latest &&
      t >= latest.at &&
      (latest.responseAt === null
        ? t < latest.clearedAt
        : t < latest.responseAt);
    let phase = "WAIT_ENDPOINTS";
    if (t >= endpointAt)
      phase = pending
        ? "QUERYING"
        : response?.busy
          ? "WAIT_IDLE"
          : "WAIT_STATE";
    if (sent) phase = "GOAL_SENT";
    if (accepted) phase = "WAIT_RESULT";
    if (done) phase = "SUCCEEDED";
    if (startupTimedOut) phase = "STARTUP_TIMEOUT";
    if (resultTimedOut) phase = "RESULT_UNCONFIRMED";
    return {
      phase,
      endpointAt,
      processStarted: t >= 1,
      serviceReady: t >= endpointAt,
      actionReady: t >= endpointAt,
      stateValid: t >= stateAt && mode !== "never",
      hasTask: (sent && !done) || t < busyUntil,
      requests: visible,
      response,
      pending: Boolean(pending),
      goalAt,
      sent,
      accepted,
      done,
      goalCount: sent ? 1 : 0,
      startupTimedOut,
      resultTimedOut,
      resultTimeoutAt,
      cancelAttempted: resultTimedOut && accepted,
      queryTimeouts: visible.filter(
        (q) => q.clearedAt !== null && t >= q.clearedAt,
      ).length,
    };
  }
  function sample(chapter, time, options = {}) {
    const o = { ...defaults(), ...options };
    const t = Math.max(0, Math.min(duration(chapter, o), time));
    let step = 0;
    chapters[chapter].steps.forEach((s, i) => {
      if (t >= s[0]) step = i;
    });
    const s = { chapter, t, options: o, step, duration: duration(chapter, o) };
    if (chapter === "build") {
      s.build = {
        source: "v2",
        installed: o.buildCase !== "stale" && t >= 2 ? "v2" : "v1",
        built: o.buildCase !== "stale" && t >= 2,
        environment: o.buildCase !== "unsourced" && t >= 4,
        ran: t >= 6,
      };
      s.build.running = s.build.ran && s.build.environment;
      s.build.error = s.build.ran && !s.build.environment;
      s.build.stale = s.build.running && s.build.installed !== s.build.source;
    }
    if (chapter === "names") s.names = names(o);
    if (chapter === "parameters") s.parameters = parameterSample(t, o);
    if (chapter === "launch")
      s.launch = {
        namespace: o.launchNamespace,
        processCount: t >= 4 ? (o.startCommand ? 4 : 3) : 0,
        started: t >= 4,
        client: o.startCommand && t >= 4,
        targetX: o.targetX,
        targetY: 0.5,
        nodes: [
          "battery_node",
          "pose_node",
          "task_manager_node",
          "command",
        ].map((n, i) => ({
          id: n,
          name: path(o.launchNamespace, n),
          enabled: i !== 3 || o.startCommand,
        })),
      };
    if (chapter === "readiness") {
      s.readiness = readinessSample(t, o);
      s.step = s.readiness.sent ? 2 : s.readiness.serviceReady ? 1 : 0;
    }
    return s;
  }
  const details = {
    source: [
      "源码文件",
      "command_node.cpp 的改动保存在源码中；构建把它编译、安装为程序。v1 / v2 仅表示不同版本。",
    ],
    install: [
      "安装结果",
      "ros2 run 找到的是已安装的可执行程序。修改源码后仍需重新构建；source 不编译代码。",
    ],
    environment: [
      "当前终端环境",
      "source install/setup.bash 让当前终端加载工作空间的安装环境。这里假定没有其他工作空间覆盖同名包。",
    ],
    process: [
      "运行进程与节点",
      "command_node 是可执行程序名；它创建的节点名为 command。一般一个进程也可以创建多个节点。",
    ],
    publisher: [
      "发布端的完整名称",
      "普通相对话题名按命名空间展开，不会自动追加节点名。图中类型与 QoS 假设兼容。",
    ],
    subscriber: [
      "订阅端的完整名称",
      "两端名称不同，无法匹配同一个话题。名称相同后，还需要类型与 QoS 等条件兼容。",
    ],
    namespace: [
      "命名空间与重映射",
      "先把相对名称展开为完整名称，再应用对应的重映射规则。另例 robot_pose.header.frame_id 是位置消息内容，不受这一步影响；电量 Int32 没有此字段。",
    ],
    parameter: [
      "参数存储值",
      "参数属于具体节点。参数服务接受更新，仍不代表某个已创建的定时器自动使用了新值。",
    ],
    timer: [
      "正在运行的定时器",
      "现有电量节点在构造时创建定时器。可写参数的教学对照里，只有显式重配置才改变脉冲间隔。",
    ],
    recipe: [
      "launch.py 启动描述",
      "实际文件把启动参数、条件和节点动作组织成 LaunchDescription。浏览器只演示求值，不执行该 Python 文件。",
    ],
    command: [
      "客户端的启动配置",
      "start_command 由 IfCondition 求值；target_x / target_y 经 ParameterValue 转成浮点数后传给 command。",
    ],
    server: [
      "进程与端点是两种状态",
      "服务端进程创建之后，Service / Action 还需要注册并能被客户端发现，固定延时不能保证业务就绪。",
    ],
    gate: [
      "发送目标之前的检查",
      "客户端先确认服务与动作端就绪，再查询 valid 和 has_task。等待过程中的查询可重试，运动目标发送一次。",
    ],
    result: [
      "超时与最终结果",
      "收到结果才能确认任务结论；结果超时会尝试取消已知目标并报告未确认，不自动重新提交运动请求。",
    ],
  };
  window.ROS2LaunchLab = {
    chapters,
    defaults,
    duration,
    sample,
    names,
    details,
  };
})();
