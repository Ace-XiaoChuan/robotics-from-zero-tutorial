(() => {
  "use strict";
  const lab = window.ROS2LaunchLab,
    $ = (id) => document.getElementById(id);
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = {
    chapter: "build",
    time: 0,
    playing: !reduced,
    speed: 1,
    options: lab.defaults(),
    selected: null,
  };
  const order = Object.keys(lab.chapters),
    scene = lab.createScene();
  let previousFrame = null,
    previousDraw = -1,
    lastAnnouncement = "";
  const setText = (id, value) => {
    const el = $(id);
    if (el && el.textContent !== String(value)) el.textContent = value;
  };
  const formatTime = (t) =>
    `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(Math.floor(t % 60)).padStart(2, "0")}`;
  const f = (v) => (Number.isFinite(v) ? String(Number(v.toFixed(4))) : "NaN");
  const kv = (key, id, value = "—") =>
    `<div class="kv"><span>${key}</span><b id="${id}">${value}</b></div>`;
  const select = (id, title, items, value) =>
    `<label class="launch-control">${title}<select id="${id}">${items.map(([v, label]) => `<option value="${v}"${String(v) === String(value) ? " selected" : ""}>${label}</option>`).join("")}</select></label>`;
  const check = (id, title, checked) =>
    `<label class="launch-control" for="${id}">${title}<input id="${id}" type="checkbox"${checked ? " checked" : ""}></label>`;
  const phases = {
    WAIT_ENDPOINTS: "等端点",
    QUERYING: "查询处理中",
    WAIT_STATE: "等有效状态",
    WAIT_IDLE: "等任务空闲",
    GOAL_SENT: "已发送目标",
    WAIT_RESULT: "等最终结果",
    SUCCEEDED: "SUCCEEDED",
    STARTUP_TIMEOUT: "启动超时",
    RESULT_UNCONFIRMED: "结果未确认",
  };
  function syncPlay() {
    const ended = state.time >= lab.duration(state.chapter, state.options);
    setText("play-icon", state.playing ? "Ⅱ" : ended ? "↺" : "▶");
    $("play").setAttribute(
      "aria-label",
      state.playing ? "暂停演示" : ended ? "重新播放本章" : "播放演示",
    );
  }
  function resetTime() {
    state.time = 0;
    state.playing = !reduced;
    state.selected = null;
    previousDraw = -1;
    syncPlay();
  }
  function bindSelect(id, property, parse = (v) => v, restart = true) {
    $(id).addEventListener("change", (e) => {
      state.options[property] = parse(e.target.value);
      if (restart) resetTime();
      else {
        state.time = Math.max(
          state.time,
          state.chapter === "names" ? 5.6 : 4.2,
        );
        state.playing = false;
        previousDraw = -1;
        syncPlay();
      }
    });
  }
  function bindCheck(id, property) {
    $(id).addEventListener("change", (e) => {
      state.options[property] = e.target.checked;
      state.time = Math.max(state.time, state.chapter === "names" ? 5.6 : 4.2);
      state.playing = false;
      previousDraw = -1;
      syncPlay();
    });
  }
  function setupPanel() {
    const o = state.options,
      chapter = state.chapter;
    const body = $("inspector-body"),
      controls = $("experiment-controls");
    controls.innerHTML = "";
    if (chapter === "build") {
      setText("inspector-title", "SOURCE / INSTALL / PROCESS");
      body.innerHTML =
        kv("源码版本", "source-version", "v2") +
        kv("安装版本", "install-version") +
        kv("工作空间环境", "environment-loaded") +
        kv("运行版本", "running-version") +
        kv("节点完整名", "running-node") +
        '<p class="code-line">ros2 run ros2_comm_demo command_node</p><p class="tiny-note">v1 / v2 是教学标记；本例假设没有其他工作空间覆盖同名包。</p>';
      controls.innerHTML = select(
        "build-case",
        "选择一条启动路径",
        [
          ["fresh", "构建 + source + run"],
          ["stale", "漏构建：只 source + run"],
          ["unsourced", "已构建：漏 source"],
        ],
        o.buildCase,
      );
      bindSelect("build-case", "buildCase");
    } else if (chapter === "names") {
      setText("inspector-title", "RESOLVED NAMES");
      body.innerHTML =
        kv("节点完整名", "node-name") +
        kv("发布端完整话题", "published-name") +
        kv("订阅端完整话题", "subscribed-name") +
        kv("名称匹配", "name-match") +
        kv("位置消息 frame_id", "frame-id", "map") +
        '<p class="tiny-note">电量 Int32 没有 frame_id；此处另取 robot_pose 的位置消息作对照。名称图假设消息类型和 QoS 兼容。</p>';
      controls.innerHTML =
        select(
          "namespace",
          "发布节点命名空间",
          [
            ["arm_a", "arm_a"],
            ["arm_b", "arm_b"],
            ["", "根命名空间 / "],
          ],
          o.namespace,
        ) +
        check("rename", "节点重命名为 battery_monitor", o.rename) +
        check("absolute", "源码使用绝对名 /battery_level", o.absolute) +
        check("remap", "规则 battery_level → battery_percent", o.remap) +
        check(
          "match-subscriber",
          "将订阅名称改为发布端完整名",
          o.matchSubscriber,
        );
      bindSelect("namespace", "namespace", (v) => v, false);
      for (const [id, key] of [
        ["rename", "rename"],
        ["absolute", "absolute"],
        ["remap", "remap"],
        ["match-subscriber", "matchSubscriber"],
      ])
        bindCheck(id, key);
    } else if (chapter === "parameters") {
      setText("inspector-title", "PARAMETER VALUE ≠ ACTIVE TIMER");
      body.innerHTML =
        kv("实现模式", "param-mode") +
        kv("启动周期", "startup-period") +
        kv("请求修改为", "requested-period") +
        kv("参数存储值", "stored-period") +
        kv("定时器周期", "timer-period") +
        kv("本次改参结果", "param-result") +
        '<p class="tiny-note" id="parameter-note"></p>';
      controls.innerHTML =
        select(
          "startup-period-control",
          "启动周期",
          [
            [0.2, "0.2 s（默认）"],
            [0.5, "0.5 s"],
            [0.0005, "0.0005 s（非法）"],
          ],
          o.period,
        ) +
        select(
          "param-mode-control",
          "实现模式",
          [
            ["readonly", "现有电量节点：只读"],
            ["store_only", "教学对照：只改存储值"],
            ["reconfigure", "教学对照：重建定时器"],
          ],
          o.paramMode,
        ) +
        '<button class="experiment-button" id="runtime-update">跳到运行中改参 →</button><button class="experiment-button primary" id="restart-period">换周期并重启 →</button>';
      bindSelect("startup-period-control", "period", Number);
      bindSelect("param-mode-control", "paramMode");
      $("runtime-update").addEventListener("click", () => {
        state.time = 4;
        state.playing = !reduced;
        previousDraw = -1;
        syncPlay();
      });
      $("restart-period").addEventListener("click", () => {
        state.options.period = o.period === 0.5 ? 0.2 : 0.5;
        state.options.paramMode = "readonly";
        setupPanel();
        resetTime();
      });
    } else if (chapter === "launch") {
      setText("inspector-title", "LAUNCH ARGUMENTS → NODE OPTIONS");
      body.innerHTML =
        '<pre class="code-block" id="launch-command"></pre><div class="divider"></div>' +
        kv("创建进程数", "process-count") +
        kv("客户端是否创建", "client-created") +
        kv("客户端目标", "launch-target") +
        kv("battery 周期", "battery-default", "0.2 s（未被覆盖）") +
        '<p class="tiny-note">target_x 由 ParameterValue 显式转成 float。目标的坐标系沿用节点配置，namespace 不修改 frame_id。</p>';
      controls.innerHTML =
        select(
          "launch-namespace",
          "整组节点命名空间",
          [
            ["lesson1", "lesson1（源码默认）"],
            ["arm_a", "arm_a"],
            ["arm_b", "arm_b"],
          ],
          o.launchNamespace,
        ) +
        select(
          "target-x",
          "客户端 target_x",
          [
            [1, "1.0 m（默认）"],
            [2, "2.0 m"],
          ],
          o.targetX,
        ) +
        check("start-command", "start_command：创建客户端", o.startCommand);
      bindSelect("launch-namespace", "launchNamespace", (v) => v, false);
      bindSelect("target-x", "targetX", Number, false);
      bindCheck("start-command", "startCommand");
    } else {
      setText("inspector-title", "READINESS / RETRY / SINGLE GOAL");
      body.innerHTML =
        kv("Service / Action 就绪", "endpoint-ready") +
        kv("最近响应 valid / busy", "valid-busy") +
        kv("状态查询次数", "query-count") +
        kv("查询超时清理次数", "query-timeouts") +
        kv("已发运动目标数", "goal-count") +
        kv("客户端阶段", "client-phase") +
        kv("结果超时取消尝试", "cancel-attempt") +
        '<p class="tiny-note" id="readiness-note"></p>';
      controls.innerHTML =
        select(
          "ready-case",
          "选择启动情形",
          [
            ["normal", "正常：状态稍晚就绪"],
            ["busy", "先有其他任务：等到空闲"],
            ["query_timeout", "首次状态查询无响应"],
            ["never", "始终无法发现两个端点"],
            ["result_timeout", "目标已接受：结果无响应"],
          ],
          o.readyCase,
        ) +
        '<button class="experiment-button primary" id="next-event">停在下一个关键事件 →</button>';
      bindSelect("ready-case", "readyCase");
      $("next-event").addEventListener("click", () => {
        const r = lab.sample("readiness", state.time, state.options).readiness;
        const markers = [
          1.01,
          2.01,
          2.18,
          4.21,
          4.59,
          5.2,
          6.8,
          7.7,
          ...(r.goalAt !== null
            ? [r.goalAt + 0.05, r.goalAt + 0.3, r.goalAt + 2.4]
            : []),
          ...(o.readyCase === "never" ? [30.25] : []),
          ...(o.readyCase === "result_timeout"
            ? [r.resultTimeoutAt + 0.05]
            : []),
        ]
          .filter(
            (v) => v > state.time + 0.03 && v <= lab.duration("readiness", o),
          )
          .sort((a, b) => a - b);
        state.time = markers[0] ?? lab.duration("readiness", o);
        state.playing = false;
        previousDraw = -1;
        syncPlay();
      });
    }
  }
  function enterChapter(id) {
    state.chapter = id;
    state.options = lab.defaults();
    state.selected = null;
    const c = lab.chapters[id];
    document.querySelectorAll("[data-chapter]").forEach((b) => {
      const active = b.dataset.chapter === id;
      b.classList.toggle("active", active);
      if (active) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    setText("panel-number", `${c.number} / 04`);
    setText("panel-kind", c.kind);
    setText("stage-kind", c.stage);
    setText("stage-context", c.context);
    $("lesson-title").innerHTML = c.title;
    setText("lesson-description", c.description);
    setText("timeline-label", c.label);
    $("steps").innerHTML = c.steps
      .map(
        (s, i) =>
          `<li><span>${i + 1}</span><div><b>${s[1]}</b><small>${s[2]}</small></div></li>`,
      )
      .join("");
    $("takeaway").innerHTML = c.takeaway;
    $("next-chapter").innerHTML = `${c.next} <span aria-hidden="true">→</span>`;
    setupPanel();
    resetTime();
    lastAnnouncement = "";
  }
  function updatePanel(s) {
    const status = $("inspector-status");
    status.className = "status-pill";
    if (s.chapter === "build") {
      const b = s.build;
      setText("install-version", b.installed);
      setText("environment-loaded", b.environment ? "已加载" : "未加载");
      setText(
        "running-version",
        b.running ? b.installed : b.error ? "未找到程序" : "未启动",
      );
      setText("running-node", b.running ? "/command" : "—");
      setText(
        "inspector-status",
        b.error
          ? "环境缺失"
          : b.stale
            ? "仍为旧程序"
            : b.running
              ? "已运行"
              : "准备中",
      );
      status.classList.toggle("bad", b.error || b.stale);
    } else if (s.chapter === "names") {
      const n = s.names;
      setText("node-name", n.node);
      setText("published-name", n.published);
      setText("subscribed-name", n.subscribed);
      setText("name-match", n.matched ? "是（类型 / QoS 另检）" : "否");
      $("name-match").classList.toggle("bad", !n.matched);
      setText("inspector-status", n.matched ? "名称匹配" : "名称不匹配");
      status.classList.toggle("bad", !n.matched);
    } else if (s.chapter === "parameters") {
      const p = s.parameters;
      setText(
        "param-mode",
        {
          readonly: "源码：只读",
          store_only: "假想：仅存储",
          reconfigure: "假想：重建定时器",
        }[p.mode],
      );
      setText("startup-period", `${f(s.options.period)} s`);
      setText("requested-period", `${f(p.requested)} s`);
      setText("stored-period", `${f(p.stored)} s`);
      setText("timer-period", p.started ? `${f(p.timer)} s` : "未创建");
      setText(
        "param-result",
        !p.valid && s.t >= 1.6
          ? "配置错误并退出"
          : p.applied
            ? p.accepted
              ? "成功"
              : "拒绝（read_only）"
            : p.attempted
              ? "请求在途"
              : "尚未请求",
      );
      setText(
        "inspector-status",
        !p.valid && s.t >= 1.6
          ? "配置错误"
          : p.applied
            ? p.accepted
              ? "写入成功"
              : "拒绝更新"
            : "观察周期",
      );
      status.classList.toggle(
        "bad",
        (!p.valid && s.t >= 1.6) || (p.applied && !p.accepted),
      );
      setText(
        "parameter-note",
        p.mode === "readonly"
          ? "这是仓库实际电量节点。启动时读取参数，运行中写入被拒绝；换启动值并重启才创建新定时器。"
          : p.mode === "store_only"
            ? "假想可写节点：参数服务接受新值，但没有重配置定时器，所以发布仍保持旧间隔。"
            : "假想可写节点：更新成功后显式重建定时器，新周期从重建时刻重新计时。两种可写模式均不是当前电量源码。",
      );
      $("runtime-update").disabled = !p.valid || s.t >= 4;
      setText(
        "restart-period",
        `以 ${s.options.period === 0.5 ? "0.2" : "0.5"} s 重启 →`,
      );
    } else if (s.chapter === "launch") {
      const l = s.launch;
      setText(
        "launch-command",
        `ros2 launch ros2_comm_demo launch.py namespace:=${s.options.launchNamespace} start_command:=${s.options.startCommand} target_x:=${s.options.targetX.toFixed(1)}`,
      );
      setText("process-count", l.processCount);
      setText(
        "client-created",
        l.client
          ? "是"
          : s.options.startCommand
            ? "等待创建"
            : "否（条件为 false）",
      );
      setText(
        "launch-target",
        s.options.startCommand
          ? `(${l.targetX.toFixed(1)}, 0.5) m`
          : "无客户端接收此参数",
      );
      setText(
        "inspector-status",
        l.started ? `${l.processCount} 个进程` : "求值配置",
      );
    } else {
      const r = s.readiness;
      setText(
        "endpoint-ready",
        r.serviceReady && r.actionReady ? "均就绪" : "等待",
      );
      setText(
        "valid-busy",
        r.response ? `${r.response.valid} / ${r.response.busy}` : "尚无响应",
      );
      setText("query-count", r.requests.length);
      setText("query-timeouts", r.queryTimeouts);
      setText("goal-count", r.goalCount);
      setText("client-phase", phases[r.phase]);
      setText(
        "cancel-attempt",
        r.cancelAttempted ? "已尝试，结果未确认" : "未尝试",
      );
      setText("inspector-status", phases[r.phase]);
      status.classList.toggle("bad", r.startupTimedOut || r.resultTimedOut);
      const pending = r.requests.at(-1);
      setText(
        "readiness-note",
        r.resultTimedOut
          ? "结果超过 20 s 未返回。已知目标句柄存在，因此尝试取消；不会自动重发，也不能据此确认已停止。"
          : r.startupTimedOut
            ? "超过默认 30 s 启动等待期限后取消检查定时器。没有发送运动目标。"
            : r.queryTimeouts > 0
              ? "首次查询超过 2 s 后清理 pending 请求，下一次定时检查再查询。目标仍只发送一次。"
              : pending && pending.responseAt === null
                ? "当前查询无响应，先等待；超过 2 s 才清理并允许下一次查询。"
                : "每 0.2 s 检查就绪；收到 valid=true 且 has_task=false 的响应后才发送目标。图中时刻为教学假设。",
      );
    }
  }
  function render(now) {
    const dt =
      previousFrame === null ? 0 : Math.min((now - previousFrame) / 1000, 0.1);
    previousFrame = now;
    const end = lab.duration(state.chapter, state.options);
    if (state.playing) {
      state.time = Math.min(end, state.time + dt * state.speed);
      if (state.time >= end) {
        state.playing = false;
        syncPlay();
      }
    }
    if (previousDraw < 0 || now - previousDraw >= 50) {
      previousDraw = now;
      const s = lab.sample(state.chapter, state.time, state.options),
        visual = scene.draw(s);
      updatePanel(s);
      const detail = state.selected ? lab.details[state.selected] : null;
      setText("figure-title", detail ? detail[0] : visual.title);
      setText("figure-note", detail ? detail[1] : visual.note);
      $("detail-reset").hidden = !detail;
      $("timeline").max = String(end);
      $("timeline").value = String(state.time);
      $("timeline").style.setProperty(
        "--progress",
        `${(state.time / end) * 100}%`,
      );
      $("timeline").setAttribute(
        "aria-valuetext",
        `${state.time.toFixed(1)} 秒，共 ${end} 秒模型时间`,
      );
      setText("time-label", `${formatTime(state.time)} / ${formatTime(end)}`);
      [...$("steps").children].forEach((li, i) => {
        li.classList.toggle("current", i === s.step);
        li.classList.toggle("done", i < s.step);
        if (i === s.step) li.setAttribute("aria-current", "step");
        else li.removeAttribute("aria-current");
      });
      const announce = `${s.chapter}/${s.step}/${s.readiness?.phase ?? ""}/${s.parameters?.applied ?? ""}`;
      if (announce !== lastAnnouncement) {
        lastAnnouncement = announce;
        setText(
          "announcement",
          `${lab.chapters[s.chapter].steps[s.step][1]}；${$("inspector-status").textContent}`,
        );
      }
    }
    requestAnimationFrame(render);
  }
  function toggle() {
    if (state.time >= lab.duration(state.chapter, state.options))
      state.time = 0;
    state.playing = !state.playing;
    syncPlay();
  }
  document
    .querySelectorAll("[data-chapter]")
    .forEach((b) =>
      b.addEventListener("click", () => enterChapter(b.dataset.chapter)),
    );
  $("play").addEventListener("click", toggle);
  $("replay").addEventListener("click", resetTime);
  $("next-chapter").addEventListener("click", () =>
    enterChapter(order[(order.indexOf(state.chapter) + 1) % order.length]),
  );
  $("timeline").addEventListener("input", (e) => {
    state.time = Number(e.target.value);
    state.playing = false;
    previousDraw = -1;
    syncPlay();
  });
  $("speed").addEventListener("change", (e) => {
    state.speed = Number(e.target.value);
  });
  const chooseDetail = (target) => {
    const el = target.closest("[data-detail]");
    if (el) {
      state.selected = el.dataset.detail;
      previousDraw = -1;
    }
  };
  $("diagram").addEventListener("click", (e) => chooseDetail(e.target));
  $("diagram").addEventListener("keydown", (e) => {
    if (
      ["Enter", " "].includes(e.key) &&
      e.target.hasAttribute("data-detail")
    ) {
      e.preventDefault();
      chooseDetail(e.target);
    }
  });
  $("detail-reset").addEventListener("click", () => {
    state.selected = null;
    previousDraw = -1;
  });
  window.addEventListener("keydown", (e) => {
    if (!["BODY", "svg"].includes(document.activeElement.tagName)) return;
    if (e.code === "Space") {
      e.preventDefault();
      toggle();
    }
    if (["ArrowLeft", "ArrowRight"].includes(e.code)) {
      e.preventDefault();
      state.time = Math.max(
        0,
        Math.min(
          lab.duration(state.chapter, state.options),
          state.time + (e.code === "ArrowRight" ? 0.25 : -0.25),
        ),
      );
      state.playing = false;
      previousDraw = -1;
      syncPlay();
    }
  });
  window.addEventListener("resize", () => {
    previousDraw = -1;
  });
  document.addEventListener("visibilitychange", () => {
    previousFrame = null;
  });
  enterChapter("build");
  requestAnimationFrame(render);
})();
