/* SVG 流程图共享时间模型；移动端改用纵向布局，标签保持可读。 */
(() => {
  "use strict";
  const lab = window.ROS2LaunchLab;
  const esc = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const label = (x, y, value, cls = "", anchor = "start") =>
    `<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}">${esc(value)}</text>`;
  const line = (x1, y1, x2, y2, bad = false) =>
    `<path d="M${x1} ${y1}L${x2} ${y2}" class="wire${bad ? " muted-wire" : ""}"${bad ? ' style="stroke:#c48a74"' : ""}/>`;
  function card(x, y, w, h, id, kicker, title, lines = [], status = "idle") {
    const color = {
      idle: "#3a5b54",
      active: "#b8c6a0",
      bad: "#c78c73",
      blue: "#87aeb8",
    }[status];
    return `<g class="entity" data-detail="${id}" tabindex="0" role="button" aria-label="查看${esc(title)}说明"><rect class="card-bg" x="${x}" y="${y}" width="${w}" height="${h}" rx="5" fill="${status === "active" ? "#28473f" : "#18332f"}" stroke="${color}"/><circle cx="${x + w - 16}" cy="${y + 17}" r="3" fill="${color}"/>${label(x + 16, y + 19, kicker, "kicker")}${label(x + 16, y + 43, title, "card-title")}${lines.map((v, i) => label(x + 16, y + 66 + i * 17, v[0] ?? v, v[1] ?? "sub")).join("")}</g>`;
  }
  function stripe(x, y, w, title, value, color = "green") {
    return `<rect x="${x}" y="${y}" width="${w}" height="30" rx="3" fill="#91ad8620"/>${label(x + 11, y + 20, title, "tiny")}${label(x + w - 11, y + 20, value, color, "end")}`;
  }
  function movingDot(x1, y1, x2, y2, progress, color = "#efbc81", text = "") {
    const x = x1 + (x2 - x1) * progress,
      y = y1 + (y2 - y1) * progress;
    return `<circle cx="${x}" cy="${y}" r="4" fill="${color}"/>${text ? label(x, y - 12, text, "tiny", "middle") : ""}`;
  }
  const period = (v) =>
    Number.isFinite(v) ? `${v < 0.001 ? v : v.toFixed(1)} s` : "NaN";
  function build(s, mobile) {
    const b = s.build,
      W = mobile ? 400 : 900,
      w = mobile ? 360 : 330,
      h = mobile ? 96 : 136;
    const positions = mobile
      ? [
          [20, 0],
          [20, 128],
          [20, 256],
          [20, 384],
        ]
      : [
          [50, 40],
          [520, 40],
          [520, 300],
          [50, 300],
        ];
    const content = [
      [
        "source",
        "01 / SOURCE",
        "command_node.cpp",
        [
          ["编辑后的源码：v2", "orange"],
          [b.built ? "源码已构建并安装" : "等待重新构建", "sub"],
        ],
        "active",
      ],
      [
        "install",
        "02 / INSTALL",
        "command_node",
        [
          [`已安装程序：${b.installed}`, b.built ? "green" : "orange"],
          [b.built ? "构建与安装完成" : "仍是旧的安装结果", "sub"],
        ],
        b.built ? "active" : "idle",
      ],
      [
        "environment",
        "03 / CURRENT TERMINAL",
        "工作空间查找环境",
        [
          [
            b.environment ? "当前终端：已 source" : "当前终端：未 source",
            b.environment ? "green" : "bad",
          ],
          ["source install/setup.bash", "mono"],
        ],
        s.t >= 4 ? (b.environment ? "active" : "bad") : "idle",
      ],
      [
        "process",
        "04 / RUNNING PROCESS",
        b.error ? "程序未找到" : "程序 → 节点",
        [
          [
            b.ran
              ? b.error
                ? "ros2 run：包不可见"
                : `${b.installed} → /command`
              : "等待 ros2 run",
            b.error ? "bad" : b.stale ? "orange" : "green",
          ],
          [
            b.stale
              ? "源码是 v2，运行的仍是 v1"
              : b.running
                ? "节点名不同于程序名"
                : "ros2_comm_demo / command_node",
            "sub",
          ],
        ],
        b.error ? "bad" : b.running ? "active" : "idle",
      ],
    ];
    let svg = "";
    positions.forEach(([x, y], i) => {
      svg += card(x, y, w, h, ...content[i]);
    });
    if (mobile) {
      for (let i = 0; i < 3; i++) {
        svg += line(200, positions[i][1] + h, 200, positions[i + 1][1]);
        svg += label(
          217,
          positions[i][1] + h + 21,
          [
            s.options.buildCase === "stale" ? "漏掉 build" : "colcon build",
            s.options.buildCase === "unsourced" ? "漏掉 source" : "source",
            "ros2 run",
          ][i],
          "tiny",
        );
      }
    } else {
      svg +=
        line(380, 108, 520, 108) +
        label(
          450,
          91,
          s.options.buildCase === "stale" ? "漏掉构建" : "colcon build",
          "tiny",
          "middle",
        );
      svg +=
        line(685, 176, 685, 300) +
        label(
          700,
          240,
          s.options.buildCase === "unsourced" ? "漏掉 source" : "source",
          "tiny",
        );
      svg +=
        line(520, 368, 380, 368) +
        label(450, 350, "ros2 run", "tiny", "middle");
      svg += label(
        50,
        251,
        "文件更新、环境加载与进程启动，各自发生在不同位置。",
        "sub",
      );
    }
    const at = s.t >= 6 ? 6 : s.t >= 4 ? 4 : 2,
      progress = (s.t - at) / 0.7;
    let moving = "";
    if (
      progress >= 0 &&
      progress < 1 &&
      !(at === 2 && s.options.buildCase === "stale") &&
      !(at === 4 && !b.environment) &&
      !(at === 6 && !b.running)
    ) {
      if (mobile) {
        const i = at === 2 ? 0 : at === 4 ? 1 : 2;
        moving = movingDot(
          200,
          positions[i][1] + h,
          200,
          positions[i + 1][1],
          progress,
        );
      } else if (at === 2 && s.options.buildCase !== "stale")
        moving = movingDot(380, 108, 520, 108, progress);
      else if (at === 4 && b.environment)
        moving = movingDot(685, 176, 685, 300, progress);
      else if (at === 6 && b.running)
        moving = movingDot(520, 368, 380, 368, progress);
    }
    return {
      svg,
      moving,
      width: W,
      title: b.error
        ? "当前终端没有找到案例包"
        : b.stale
          ? "改了源码，但仍运行旧程序"
          : b.running
            ? "成功运行已安装的程序"
            : "从源码到运行节点",
      note: b.error
        ? "本例假设只加载了 ROS 基础环境；加载案例工作空间后再启动。"
        : b.stale
          ? "source 已完成，但不会替代构建。重新构建并安装才能更新程序。"
          : "点击卡片，区分源文件、安装结果、当前终端环境和运行进程。",
    };
  }
  function names(s, mobile) {
    const n = s.names;
    let svg = "",
      moving = "";
    if (mobile) {
      svg += card(
        18,
        0,
        364,
        106,
        "publisher",
        "PUBLISHER",
        n.node,
        [
          [s.t >= 2 ? n.published : n.source, "orange"],
          ["std_msgs/msg/Int32", "tiny"],
        ],
        "active",
      );
      svg += card(
        18,
        162,
        364,
        106,
        "subscriber",
        "SUBSCRIBER",
        "task_manager_node",
        [
          [n.subscribed, n.matched ? "green" : "bad"],
          ["图中假设消息类型、QoS 兼容", "tiny"],
        ],
        s.t >= 5 ? (n.matched ? "active" : "bad") : "idle",
      );
      svg +=
        line(200, 106, 200, 162, !n.matched) +
        label(
          217,
          139,
          s.t >= 5 ? (n.matched ? "名称匹配" : "名称不匹配") : "比较完整名称",
          n.matched ? "green" : "bad",
        );
      svg += card(
        18,
        305,
        364,
        165,
        "namespace",
        "RESOLUTION",
        "相对名与重映射",
        [
          [`源码：${n.source}`, "mono"],
          [`展开：${n.original}`, "mono"],
          [`结果：${n.published}`, "orange"],
          ["另例 robot_pose：frame_id = map", "sub"],
        ],
        s.t >= 2 ? "active" : "idle",
      );
      if (n.matched && s.t >= 5.5) {
        const p = ((s.t - 5.5) % 1.4) / 0.9;
        if (p < 1) moving = movingDot(200, 106, 200, 162, p, "#adcfa2");
      }
    } else {
      svg += card(
        45,
        55,
        350,
        155,
        "publisher",
        "PUBLISHER",
        n.node,
        [
          [s.t >= 2 ? n.published : n.source, "orange"],
          ["std_msgs/msg/Int32", "tiny"],
          ["节点名独立于普通相对话题名", "sub"],
        ],
        "active",
      );
      svg += card(
        505,
        55,
        350,
        155,
        "subscriber",
        "SUBSCRIBER",
        "task_manager_node",
        [
          [n.subscribed, n.matched ? "green" : "bad"],
          ["std_msgs/msg/Int32", "tiny"],
          ["图中假设类型与 QoS 兼容", "sub"],
        ],
        s.t >= 5 ? (n.matched ? "active" : "bad") : "idle",
      );
      svg +=
        line(395, 137, 505, 137, !n.matched) +
        label(
          450,
          118,
          s.t >= 5 ? (n.matched ? "名称匹配" : "名称不匹配") : "比较名称",
          n.matched ? "green" : "bad",
          "middle",
        );
      svg += card(
        45,
        280,
        810,
        160,
        "namespace",
        "NAME RESOLUTION",
        "同一条规则，展开后再比较",
        [
          [`源码 ${n.source}   →   展开 ${n.original}`, "mono"],
          [
            s.options.remap
              ? `规则 ${n.ruleFrom} → ${n.ruleTo}`
              : "未配置重映射规则",
            "mono",
          ],
          [`发布结果 ${n.published}`, "orange"],
          ["另例 robot_pose：header.frame_id = map", "sub"],
        ],
        s.t >= 2 ? "active" : "idle",
      );
      if (n.matched && s.t >= 5.5) {
        const p = ((s.t - 5.5) % 1.4) / 0.9;
        if (p < 1) {
          moving = movingDot(395, 137, 505, 137, p, "#adcfa2");
          svg += label(450, 162, "data: 100", "tiny", "middle");
        }
      }
    }
    return {
      svg,
      moving,
      width: mobile ? 400 : 900,
      title:
        s.t >= 5
          ? n.matched
            ? "两端指向同一个完整话题名"
            : "两端名称不同，话题无法匹配"
          : "从源码里的名称，解析到 ROS 图中的名称",
      note: n.remapped
        ? `${n.source} 应用规则后成为 ${n.published}。更改节点名不改变这个普通相对话题名。`
        : `本条话题未应用重映射，完整名为 ${n.published}。绝对名是否匹配规则，要比较规则展开后的完整名。`,
    };
  }
  function parameters(s, mobile) {
    const p = s.parameters,
      w = mobile ? 400 : 900;
    const x1 = mobile ? 18 : 50,
      x2 = mobile ? 210 : 520,
      cw = mobile ? 172 : 330,
      h = mobile ? 155 : 155;
    let svg = card(
      x1,
      25,
      cw,
      h,
      "parameter",
      p.mode === "readonly" ? "ACTUAL / READ ONLY" : "TEACHING COMPARISON",
      "参数存储值",
      [
        ["publish_period_s", "mono"],
        [period(p.stored), "orange"],
        [
          p.mode === "readonly" ? "read_only = true" : "可写参数（假想节点）",
          "tiny",
        ],
      ],
      p.applied && !p.accepted ? "bad" : "active",
    );
    svg += card(
      x2,
      25,
      cw,
      h,
      "timer",
      "ACTIVE TIMER",
      p.valid ? "实际定时器" : "构造失败",
      [
        [
          p.started ? period(p.timer) : p.valid ? "尚未创建" : "没有定时器",
          "green",
        ],
        [
          p.started
            ? `目标频率 ${(1 / p.timer).toFixed(1)} Hz`
            : p.valid
              ? "等待构造"
              : "exit = 1",
          "sub",
        ],
        ["其他节点参数独立", "tiny"],
      ],
      !p.valid && s.t >= 1.6 ? "bad" : p.started ? "active" : "idle",
    );
    if (!mobile)
      svg +=
        line(380, 104, 520, 104, p.applied && p.mode !== "reconfigure") +
        label(
          450,
          86,
          p.applied ? (p.accepted ? "更新成功" : "更新被拒绝") : "构造时读取",
          p.applied && !p.accepted ? "bad" : "sub",
          "middle",
        );
    const px = mobile ? 23 : 58,
      py = mobile ? 267 : 290,
      pw = mobile ? 354 : 784,
      base = py + 90;
    svg += label(px, py - 17, "IDEAL TIMER EVENTS / 理想发布时刻", "kicker");
    svg += `<rect x="${px}" y="${py}" width="${pw}" height="119" rx="4" fill="#0f2528" stroke="#3b5d50"/>`;
    const timeX = (t) => px + ((t - 2) / 8) * pw;
    for (let second = 2; second <= 10; second += 2) {
      const x = timeX(second);
      svg +=
        `<path d="M${x} ${py + 10}V${base}" stroke="#4e6b5e" opacity=".45"/>` +
        label(
          x,
          base + 19,
          `${second}s`,
          "tiny",
          second === 2 ? "start" : second === 10 ? "end" : "middle",
        );
    }
    svg += `<path d="M${px} ${base}H${px + pw}" stroke="#708a74"/>`;
    if (p.valid) {
      for (const pulse of p.pulses) {
        const x = timeX(pulse);
        svg += `<path d="M${x} ${base}V${base - 38}" stroke="${pulse > 4.5 && p.mode === "reconfigure" ? "#cbb283" : "#b6d1a8"}" stroke-width="2"/>`;
      }
    }
    if (p.valid && s.t >= 4) {
      const x = timeX(4.5);
      svg +=
        `<path d="M${x} ${py}V${base}" stroke="#db9d77" stroke-dasharray="3 4"/>` +
        label(
          x + 7,
          py + 19,
          p.applied
            ? p.accepted
              ? "更新响应成功"
              : "更新响应拒绝"
            : "改参请求",
          p.applied && !p.accepted ? "bad" : "orange",
        );
    }
    if (s.t >= 2 && s.t <= 10) {
      const x = timeX(s.t);
      svg += `<path d="M${x} ${py}V${base}" stroke="#edddba" opacity=".7"/>`;
    }
    if (!p.valid && s.t >= 1.6)
      svg += label(
        px + pw / 2,
        base - 26,
        "周期 < 0.001 s → 配置错误，退出",
        "bad",
        "middle",
      );
    svg += label(
      px,
      py + 148,
      p.mode === "readonly"
        ? "运行中改参被拒绝，定时器保持启动值。"
        : p.mode === "store_only"
          ? "假想对照：只存新参数，定时器保持旧周期。"
          : "假想对照：显式重建定时器，改变脉冲间隔。",
      "sub",
    );
    return {
      svg,
      moving: "",
      width: w,
      title: !p.valid
        ? "非法启动值：节点报告配置错误"
        : p.mode === "readonly"
          ? "现有实现：应用参数只在启动时配置"
          : "教学对照：区分参数存储与定时器行为",
      note: p.valid
        ? `启动周期 ${period(s.options.period)}，运行中请求 ${period(p.requested)}。图中脉冲是理想时刻，实际频率仍受执行器与系统调度影响。`
        : "common.hpp 检查参数有限且不小于 0.001 s；没有成功创建的节点，也没有发布脉冲。",
    };
  }
  function launch(s, mobile) {
    const l = s.launch,
      n = s.options.launchNamespace;
    let svg = "",
      moving = "";
    const recipeX = mobile ? 18 : 45,
      recipeY = mobile ? 0 : 90,
      recipeW = mobile ? 364 : 345,
      recipeH = mobile ? 145 : 300;
    svg += card(
      recipeX,
      recipeY,
      recipeW,
      recipeH,
      "recipe",
      "LAUNCH DESCRIPTION",
      "launch.py",
      [
        [`namespace = "${n}"`, "mono"],
        [`start_command = ${s.options.startCommand}`, "mono"],
        [`target_x = ${s.options.targetX.toFixed(1)} m`, "orange"],
        ...(!mobile
          ? [
              ["LaunchConfiguration → Node", "sub"],
              ["进程启动 ≠ 业务就绪", "sub"],
            ]
          : []),
      ],
      s.t >= 2 ? "active" : "idle",
    );
    l.nodes.forEach((node, i) => {
      const x = mobile ? (i % 2 === 0 ? 18 : 210) : 505,
        y = mobile ? 180 + Math.floor(i / 2) * 153 : 5 + i * 118,
        cw = mobile ? 172 : 350,
        ch = mobile ? 135 : 101;
      const displayTitle =
        mobile && node.id === "task_manager_node" ? "task_manager" : "";
      const lines = mobile
        ? [
            [`/${n}/`, "mono"],
            [node.id, "mono"],
            [
              i === 3
                ? node.enabled
                  ? `目标 (${s.options.targetX.toFixed(1)}, 0.5) m`
                  : "条件为 false：省略"
                : l.started
                  ? "进程已创建"
                  : "等待创建",
              node.enabled ? "green" : "bad",
            ],
          ]
        : [
            [node.name, "mono"],
            [
              i === 3
                ? node.enabled
                  ? `目标 (${s.options.targetX.toFixed(1)}, 0.5) m`
                  : "IfCondition(false)：不创建进程"
                : l.started
                  ? "进程已创建；业务就绪另行检查"
                  : "等待 Node 动作执行",
              node.enabled ? "green" : "bad",
            ],
          ];
      svg += card(
        x,
        y,
        cw,
        ch,
        i === 3 ? "command" : "process",
        `NODE ${i + 1}${node.enabled ? "" : " / SKIPPED"}`,
        displayTitle || node.id,
        lines,
        node.enabled ? (l.started ? "active" : "idle") : "bad",
      );
      if (!mobile) {
        svg += `<path d="M390 240C445 240 450 ${y + 50} 505 ${y + 50}" class="wire${node.enabled ? "" : " muted-wire"}"/>`;
        if (s.t >= 2 && s.t < 3 && node.enabled)
          moving += movingDot(390, 240, 505, y + 50, s.t - 2);
      }
    });
    return {
      svg,
      moving,
      width: mobile ? 400 : 900,
      title: `命名空间 /${n}，${s.options.startCommand ? "四个" : "三个"}进程${l.started ? "已创建" : "待创建"}`,
      note: "这里只演示 launch 配置与条件求值，节点启动顺序和接口注册时刻均为示意。目标参数只属于 command，其他节点不会共享这份参数值。",
    };
  }
  function readiness(s, mobile) {
    const r = s.readiness,
      w = mobile ? 400 : 900;
    let svg = "",
      moving = "";
    const positions = mobile
        ? [
            [18, 0],
            [18, 100],
            [18, 200],
          ]
        : [
            [35, 20],
            [330, 20],
            [625, 20],
          ],
      cw = mobile ? 364 : 240,
      ch = mobile ? 84 : 135;
    svg += card(
      ...positions[0],
      cw,
      ch,
      "server",
      "PROCESS",
      "服务端进程",
      [
        [
          r.processStarted ? "进程存在" : "等待创建",
          r.processStarted ? "green" : "sub",
        ],
        ...(!mobile ? [["本例在 t=1 s 创建", "tiny"]] : []),
      ],
      r.processStarted ? "active" : "idle",
    );
    svg += card(
      ...positions[1],
      cw,
      ch,
      "server",
      "ENDPOINTS",
      "Service + Action",
      [
        [
          r.serviceReady ? "两个端点均已就绪" : "尚未发现两个端点",
          r.serviceReady ? "green" : "orange",
        ],
        ...(!mobile ? [["客户端每 0.2 s 检查", "tiny"]] : []),
      ],
      r.serviceReady ? "active" : "idle",
    );
    svg += card(
      ...positions[2],
      cw,
      ch,
      "gate",
      "CACHED STATE",
      r.stateValid ? "有效状态" : "等待有效状态",
      [
        [
          r.stateValid ? `valid=true · busy=${r.hasTask}` : "valid=false",
          r.stateValid ? "green" : "orange",
        ],
        ...(!mobile ? [["电量与位置缓存均需有效", "tiny"]] : []),
      ],
      r.stateValid ? "active" : "idle",
    );
    const gx = mobile ? 18 : 175,
      gy = mobile ? 308 : 225,
      gw = mobile ? 364 : 550,
      gh = mobile ? 75 : 100;
    svg += `<g class="entity" data-detail="gate" tabindex="0" role="button" aria-label="查看发送目标检查说明"><rect class="card-bg" x="${gx}" y="${gy}" width="${gw}" height="${gh}" rx="5" fill="#243e34" stroke="${r.sent ? "#c2d1a2" : "#698574"}"/>${label(gx + 16, gy + 23, "SEND GOAL / 发送前检查", "kicker")}${label(gx + 16, gy + 49, r.sent ? "发送时：端点就绪、状态有效、任务空闲" : "端点就绪  ∧  valid  ∧  !has_task", r.sent ? "green" : "mono")}${!mobile ? label(gx + 16, gy + 77, "满足条件后只提交一次运动目标，查询重试与目标重发分开处理。", "sub") : ""}</g>`;
    const bx = mobile ? 18 : 35,
      by = mobile ? 406 : 380,
      bw = mobile ? 172 : 280,
      bh = mobile ? 84 : 100,
      rx = mobile ? 210 : 585;
    svg += card(
      bx,
      by,
      bw,
      bh,
      "command",
      "CLIENT",
      "command",
      [
        [`状态查询 ${r.requests.length} 次`, "sub"],
        ...(!mobile ? [[`查询超时清理 ${r.queryTimeouts} 次`, "sub"]] : []),
      ],
      r.startupTimedOut ? "bad" : "active",
    );
    const result = r.startupTimedOut
      ? "启动等待超时"
      : r.resultTimedOut
        ? "结果未确认"
        : r.done
          ? "SUCCEEDED"
          : r.sent
            ? "等待结果"
            : "尚未发送";
    svg += card(
      rx,
      by,
      bw,
      bh,
      "result",
      "ACTION GOAL",
      `运动目标 ${r.goalCount} 次`,
      [
        [
          result,
          r.resultTimedOut || r.startupTimedOut
            ? "bad"
            : r.done
              ? "green"
              : "orange",
        ],
        ...(!mobile
          ? [
              [
                r.cancelAttempted
                  ? "已尝试取消；不重发目标"
                  : "只提交一次，不自动重发",
                "sub",
              ],
            ]
          : []),
      ],
      r.startupTimedOut || r.resultTimedOut
        ? "bad"
        : r.done
          ? "active"
          : "idle",
    );
    if (mobile) {
      for (let i = 0; i < 2; i++)
        svg += line(200, positions[i][1] + ch, 200, positions[i + 1][1]);
      svg += line(200, 284, 200, 308) + line(200, 383, 296, 406);
    } else {
      svg += line(275, 87, 330, 87) + line(570, 87, 625, 87);
      svg +=
        line(745, 155, 650, 225) +
        line(175, 155, 270, 225) +
        line(315, 425, 450, 325) +
        line(450, 325, 585, 425);
    }
    const latest = r.requests.at(-1);
    if (latest && !mobile) {
      if (s.t < latest.at + 0.15)
        moving += movingDot(
          315,
          425,
          450,
          325,
          (s.t - latest.at) / 0.15,
          "#9dc5dd",
        );
      if (
        latest.responseAt &&
        s.t >= latest.responseAt &&
        s.t < latest.responseAt + 0.12
      )
        moving += movingDot(
          450,
          325,
          315,
          425,
          (s.t - latest.responseAt) / 0.12,
          "#b9d4aa",
        );
    }
    if (r.goalAt !== null && s.t >= r.goalAt && s.t < r.goalAt + 0.8)
      moving += mobile
        ? movingDot(200, 383, 296, 406, (s.t - r.goalAt) / 0.8)
        : movingDot(
            450,
            325,
            585,
            425,
            (s.t - r.goalAt) / 0.8,
            "#e8bb83",
            "Goal",
          );
    return {
      svg,
      moving,
      width: w,
      title: r.startupTimedOut
        ? "启动等待超过 30 s：停止等待，目标数仍为 0"
        : r.resultTimedOut
          ? "结果等待超过 20 s：尝试取消，结论仍未确认"
          : r.done
            ? "收到最终结果，本次启动流程结束"
            : r.sent
              ? "目标已经发出：只等待这一次交互的结果"
              : "先发现端点，再等有效且空闲的状态",
      note: r.resultTimedOut
        ? "取消请求本身也需要处理；页面保持“结果未确认”，不会把取消尝试画成已停止或自动重新发送目标。"
        : r.startupTimedOut
          ? "客户端定时器取消，启动等待不再继续；固定延时不能使缺失的服务自动就绪。"
          : "进程、端点与缓存的就绪时刻都是教学假设。查询可重试，目标计数最多为 1。",
    };
  }
  const renderers = { build, names, parameters, launch, readiness };
  lab.createScene = () => {
    let lastMarkup = "";
    return {
      draw(s) {
        const mobile = document.getElementById("stage").clientWidth < 570;
        const result = renderers[s.chapter](s, mobile);
        const root = document.getElementById("diagram");
        root.setAttribute("viewBox", `0 0 ${result.width} 490`);
        if (result.svg !== lastMarkup) {
          const focused = document.activeElement?.getAttribute("data-detail");
          document.getElementById("figure").innerHTML = result.svg;
          lastMarkup = result.svg;
          if (focused)
            document
              .querySelector(`#figure [data-detail="${focused}"]`)
              ?.focus({ preventScroll: true });
        }
        document.getElementById("moving").innerHTML = result.moving;
        return result;
      },
    };
  };
})();
