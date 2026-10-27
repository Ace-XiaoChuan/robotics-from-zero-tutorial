/* 教学时间线是纯函数：拖动进度、重播与逐帧播放得到同一状态。
 * t 是演示秒；Topic / Service 的缓存年龄按 5 倍慢放换算。
 * Action 的二维积分使用固定 0.01 s 步长，不依赖屏幕帧率。
 */
(() => {
  "use strict";
  const nodes = [
    {
      id: "battery",
      name: "battery_node",
      role: "电量发布者",
      position: [-4.4, 0, -1.8],
      color: "#f4a66c",
      detail: "按定时器发布 battery_level。发布者无需知道订阅者是谁。",
    },
    {
      id: "task",
      name: "task_manager_node",
      role: "状态缓存 · 任务执行",
      position: [0, 0, -0.6],
      color: "#bdcbb0",
      detail:
        "订阅电量与位置，缓存状态；响应 Service，并执行 Navigation Action。",
    },
    {
      id: "pose",
      name: "pose_node",
      role: "位置更新 · 速度积分",
      position: [-2.5, 0, 2.8],
      color: "#f4a66c",
      detail:
        "接收 cmd_vel，分别积分 x、y，再发布 map 中的位置；本例没有朝向或碰撞动力学。",
    },
    {
      id: "command",
      name: "command",
      role: "查询与任务客户端",
      position: [4.2, 0, 1.1],
      color: "#89bbec",
      detail:
        "程序 command_node 创建的节点名为 command。它查询状态、发送目标并处理反馈和结果。",
    },
  ];
  const edges = [
    {
      id: "battery",
      from: "battery",
      to: "task",
      kind: "topic",
      lift: 0.85,
      bend: -0.35,
    },
    {
      id: "pose",
      from: "pose",
      to: "task",
      kind: "topic",
      lift: 0.65,
      bend: -0.4,
    },
    {
      id: "velocity",
      from: "task",
      to: "pose",
      kind: "topic",
      lift: 1.0,
      bend: 0.65,
    },
    {
      id: "request",
      from: "command",
      to: "task",
      kind: "service",
      lift: 1.0,
      bend: -0.65,
    },
    {
      id: "response",
      from: "task",
      to: "command",
      kind: "service",
      lift: 0.65,
      bend: 0.35,
    },
    {
      id: "goal",
      from: "command",
      to: "task",
      kind: "action",
      lift: 1.55,
      bend: 0.45,
    },
    {
      id: "feedback",
      from: "task",
      to: "command",
      kind: "action",
      lift: 1.0,
      bend: -0.4,
    },
  ];
  const chapters = {
    nodes: {
      number: "00",
      kind: "NODE",
      title: "一个机器人，<br>四个节点。",
      label: "认识四个节点",
      duration: 12,
      description:
        "节点是承担具体职责的功能单位。先看谁在生产数据、谁在处理任务、谁在发起请求。",
      steps: [
        [0, "先分工", "battery 与 pose 分别更新电量和位置。"],
        [3, "再连接", "task_manager 接收状态，command 发起交互。"],
        [
          7,
          "按需求选择接口",
          "持续数据用 Topic；查询用 Service；任务用 Action。",
        ],
      ],
      takeaway:
        "<strong>节点不等于进程。</strong>一个进程可以创建多个节点；同一个节点也可以拥有多种通信接口。",
      next: "接下来：持续更新的 Topic",
    },
    topic: {
      number: "01",
      kind: "TOPIC",
      title: "消息持续流动，<br>状态逐次更新。",
      label: "观察发布 → 传输 → 订阅回调",
      duration: 14,
      description:
        "电量节点定时发布，任务节点在订阅回调里写入缓存。动画把 0.2 s 的周期放慢为 1 s。",
      steps: [
        [0, "定时器触发发布", "消息类型 Int32，电量范围约定为 0～100。"],
        [1.65, "订阅回调写入缓存", "新消息到达前，缓存仍保留上一次的值。"],
        [5.65, "多次更新形成数据流", "每一条消息都不需要等待业务响应。"],
      ],
      takeaway:
        "<strong>10 是 Keep Last 深度，不是 10 Hz。</strong>发布周期由定时器决定；实际接收还受 QoS 与执行器调度影响。",
      next: "接下来：Service 查询缓存",
    },
    service: {
      number: "02",
      kind: "SERVICE",
      title: "问一次，<br>返回一份快照。",
      label: "第一次查询新鲜缓存，第二次查询过期缓存",
      duration: 10,
      description:
        "两路状态在首次更新后暂停，便于观察过期。服务端读取缓存，不触发新的电量测量。",
      steps: [
        [0, "先缓存电量 99 和位置", "从收到状态开始，用单调时钟计算年龄。"],
        [
          2,
          "请求 → 读取缓存 → 响应",
          "Future 表示稍后取得的结果，响应回调仍需调度。",
        ],
        [6, "过一会儿，再查一次", "状态年龄超过 0.8 s，新的响应 valid=false。"],
      ],
      takeaway:
        "<strong>已经收到的 Response 不会自行改变。</strong>缓存年龄继续增长；只有再次查询，才得到新的快照。",
      next: "接下来：Action 执行任务",
    },
    action: {
      number: "03",
      kind: "ACTION",
      title: "接受目标之后，<br>任务才刚开始。",
      label: "Goal → 接受 → Feedback → Result",
      duration: 12,
      description:
        "目标是 map 平面中的 (1.0, 0.5) m。任务节点发速度，位置节点积分；反馈报告观测距离。",
      steps: [
        [
          0,
          "Goal 发出，服务端决定是否接受",
          "本次使用状态新鲜、电量充足的有效目标。",
        ],
        [
          1.6,
          "执行中，持续回传 Feedback",
          "cmd_vel → 位置更新 → 距离反馈形成闭环。",
        ],
        [
          9,
          "等待服务端的最终 Result",
          "到达、取消、状态失效会走向不同终止状态。",
        ],
      ],
      takeaway:
        "<strong>Feedback 是进度，Result 才是结论。</strong>取消请求也要先被接受，服务端停止执行后再报告 CANCELED。",
      next: "接下来：收到的数据能用吗？",
    },
    contracts: {
      number: "04",
      kind: "CONTRACT",
      title: "消息到了，<br>就能直接用吗？",
      label: "类型、传输与业务检查",
      duration: 6,
      description:
        "类型规定字段的结构。单位、坐标系、时间与合法范围，还需要接口约定和业务代码一起保证。",
      steps: [
        [0, "先看字段与类型", "Int32 允许 150；PointStamped 允许填 odom。"],
        [2, "消息确实到达回调", "通信成功只说明数据送到了。"],
        [
          3,
          "业务检查决定是否接收",
          "范围、坐标系或时间不符合约定，就不更新缓存。",
        ],
      ],
      takeaway:
        "<strong>类型正确、通信成功、业务正确，是三层判断。</strong>frame_id 只是标签，填写它不会创建 TF 或变换坐标。",
      next: "回到开头：重新观察整张图",
    },
  };
  const colors = { topic: "#f4a66c", service: "#89bbec", action: "#8dd8b5" };
  const packet = (time, edge, label, duration = 0.65) => ({
    time,
    edge,
    label,
    duration,
  });
  const defaultOptions = () => ({
    drain: 1,
    scenario: "range",
    cancelAt: null,
    dropoutAt: null,
  });

  // 和案例采用同样的比例限速关系；这是教学积分，不是 ROS 仿真执行记录。
  function motion(elapsed, options) {
    let x = 0,
      y = 0,
      vx = 0,
      vy = 0;
    const trail = [[0, 0]];
    let phase =
      elapsed < 0.7 ? "SENDING" : elapsed < 1.6 ? "ACCEPTED" : "EXECUTING";
    let terminalAt = null,
      terminalDistance = null;
    const cancelAcceptedAt =
      options.cancelAt === null ? Infinity : options.cancelAt + 0.55;
    const canceledAt = cancelAcceptedAt + 0.05;
    const abortedAt =
      options.dropoutAt === null ? Infinity : options.dropoutAt + 0.8;
    let lastPoseX = 0,
      lastPoseY = 0;
    // 固定步长保证拖动回放与连续播放完全一致。
    const steps = Math.floor(Math.max(0, elapsed - 1.6) / 0.01 + 1e-8);
    for (let i = 0; i <= steps && elapsed >= 1.6; i++) {
      const now = 1.6 + i * 0.01;
      const d = Math.hypot(1 - lastPoseX, 0.5 - lastPoseY);
      // 已接受取消后优先停止；若目标在取消请求抵达前已结束，则仍返回原结果。
      if (
        now >= canceledAt ||
        now >= abortedAt ||
        (d <= 0.03 && now < cancelAcceptedAt)
      ) {
        phase =
          now >= canceledAt && canceledAt <= abortedAt
            ? "CANCELED"
            : now >= abortedAt
              ? "ABORTED"
              : "SUCCEEDED";
        terminalAt = now;
        terminalDistance = d;
        vx = vy = 0;
        break;
      }
      if (i === steps) break;
      const factor = Math.min(2, 0.5 / Math.max(d, 0.0001));
      vx = factor * (1 - lastPoseX);
      vy = factor * (0.5 - lastPoseY);
      x += vx * 0.01;
      y += vy * 0.01;
      if (options.dropoutAt === null || now < options.dropoutAt) {
        lastPoseX = x;
        lastPoseY = y;
      }
      if (i % 10 === 0) trail.push([x, y]);
    }
    trail.push([x, y]);
    if (
      terminalAt === null &&
      options.cancelAt !== null &&
      elapsed >= options.cancelAt
    )
      phase = "CANCEL_REQUESTED";
    if (
      terminalAt === null &&
      options.cancelAt !== null &&
      elapsed >= options.cancelAt + 0.55
    )
      phase = "CANCELING";
    return {
      x,
      y,
      vx,
      vy,
      distance: Math.hypot(1 - lastPoseX, 0.5 - lastPoseY),
      actualDistance: Math.hypot(1 - x, 0.5 - y),
      trail,
      phase,
      terminalAt,
      terminalDistance,
      lastPoseX,
      lastPoseY,
    };
  }

  function sample(chapter, t, opts = defaultOptions()) {
    const options = { ...defaultOptions(), ...opts };
    const config = chapters[chapter];
    t = Math.max(0, Math.min(config.duration, t));
    const state = {
      chapter,
      t,
      options,
      packets: [],
      activeEdges: [],
      focus: nodes.map((n) => n.id),
      cache: null,
      cacheAge: null,
      battery: 100,
      response: null,
      motion: null,
      stage: 0,
    };
    config.steps.forEach((step, i) => {
      if (t >= step[0]) state.stage = i;
    });
    const events = [];
    if (chapter === "nodes") {
      state.focus =
        t < 3
          ? ["battery", "pose"]
          : t < 7
            ? ["task", "command"]
            : nodes.map((n) => n.id);
      state.activeEdges = t < 7 ? ["battery", "pose"] : edges.map((e) => e.id);
      for (let s = 0.5; s < 12; s += 2)
        events.push(
          packet(s, "battery", "Int32"),
          packet(s + 0.5, "pose", "PointStamped"),
        );
      if (t >= 7)
        events.push(
          packet(7.1, "request", "Request"),
          packet(7.9, "response", "Response"),
          packet(9.2, "goal", "Goal"),
          packet(10.2, "feedback", "Feedback"),
        );
    } else if (chapter === "topic") {
      state.activeEdges = ["battery", "pose"];
      state.focus = ["battery", "task", "pose"];
      let lastArrival = null;
      for (let i = 0; i < 13; i++) {
        const sent = 1 + i;
        const value = Math.max(0, 100 - i * options.drain);
        events.push(packet(sent, "battery", `data: ${value}`));
        if (t >= sent) state.battery = value;
        if (t >= sent + 0.65) {
          state.cache = value;
          lastArrival = sent + 0.65;
        }
        if (i % 2 === 0)
          events.push(packet(sent + 0.25, "pose", "map · (0, 0)"));
      }
      state.cacheAge = lastArrival === null ? null : (t - lastArrival) / 5;
    } else if (chapter === "service") {
      state.activeEdges = ["request", "response"];
      state.focus = ["command", "task"];
      if (t >= 0.6) {
        state.cache = 99;
        state.cacheAge = (t - 0.6) / 5;
      }
      for (const sent of [2, 6]) {
        events.push(
          packet(sent, "request", "Request {}", 0.7),
          packet(sent + 0.7, "response", `valid: ${sent === 2}`, 0.8),
        );
        if (t >= sent + 1.5) {
          const age = (sent + 0.7 - 0.6) / 5;
          state.response = {
            battery: 99,
            valid: age <= 0.8,
            age,
            query: sent === 2 ? 1 : 2,
            capturedAt: (sent + 0.7) / 5,
          };
        }
      }
      state.queryPending = (t >= 2 && t < 3.5) || (t >= 6 && t < 7.5);
    } else if (chapter === "action") {
      state.activeEdges = ["goal", "feedback", "velocity", "pose", "battery"];
      state.motion = motion(t, options);
      state.focus = ["command", "task", "pose"];
      state.cache = 100;
      const m = state.motion;
      events.push(
        packet(0, "goal", "Goal (1.0, 0.5)", 0.7),
        packet(0.75, "feedback", "ACCEPTED", 0.65),
      );
      for (let s = 1.6; s < (m.terminalAt ?? t) && s < 12; s += 0.65) {
        events.push(packet(s, "velocity", "cmd_vel", 0.45));
        const poseAvailable =
          options.dropoutAt === null || s < options.dropoutAt;
        if (poseAvailable)
          events.push(packet(s + 0.08, "pose", "robot_pose", 0.45));
        events.push(packet(s + 0.16, "feedback", "Feedback", 0.5));
      }
      if (options.cancelAt !== null) {
        const accepted =
          m.terminalAt === null || m.terminalAt >= options.cancelAt + 0.55;
        events.push(
          packet(options.cancelAt, "goal", "Cancel request", 0.55),
          packet(
            options.cancelAt + 0.55,
            "feedback",
            accepted ? "Cancel accepted" : "Goal already terminal",
            0.3,
          ),
        );
      }
      if (m.terminalAt !== null)
        events.push(
          packet(m.terminalAt, "velocity", "Twist = 0", 0.45),
          packet(m.terminalAt + 0.08, "feedback", m.phase, 0.65),
        );
      state.resultReceived = m.terminalAt !== null && t >= m.terminalAt + 0.73;
      state.stage = t < 1.6 ? 0 : state.resultReceived ? 2 : 1;
    } else if (chapter === "contracts") {
      const isBattery = ["range", "valid"].includes(options.scenario);
      state.activeEdges = [isBattery ? "battery" : "pose"];
      state.focus = [isBattery ? "battery" : "pose", "task"];
      state.contract = {
        range: {
          label: "Int32 · data: 150",
          input: "data: 150",
          rule: "0 ≤ data ≤ 100",
          accepted: false,
          reason: "超出电量约定范围",
          type: "std_msgs/msg/Int32",
        },
        valid: {
          label: "Int32 · data: 99",
          input: "data: 99",
          rule: "0 ≤ data ≤ 100",
          accepted: true,
          reason: "合法，写入缓存",
          type: "std_msgs/msg/Int32",
        },
        frame: {
          label: 'frame_id: "odom"',
          input: 'frame_id: "odom"',
          rule: 'expected: "map"',
          accepted: false,
          reason: "坐标系不匹配",
          type: "geometry_msgs/msg/PointStamped",
        },
        stamp: {
          label: "stamp age: 0.9 s",
          input: "producer age: 0.9 s",
          rule: "max age: 0.8 s",
          accepted: false,
          reason: "生产者时间戳过旧",
          type: "geometry_msgs/msg/PointStamped",
        },
      }[options.scenario];
      events.push(
        packet(1, isBattery ? "battery" : "pose", state.contract.label, 1),
      );
      state.cache = t >= 3 && state.contract.accepted ? 99 : 100;
    }
    state.packets = events
      .filter((e) => t >= e.time && t < e.time + e.duration)
      .map((e) => ({
        ...e,
        progress: (t - e.time) / e.duration,
        kind: edges.find((x) => x.id === e.edge).kind,
      }));
    return state;
  }
  window.ROS2Lab = {
    nodes,
    edges,
    chapters,
    colors,
    sample,
    motion,
    defaultOptions,
  };
})();
