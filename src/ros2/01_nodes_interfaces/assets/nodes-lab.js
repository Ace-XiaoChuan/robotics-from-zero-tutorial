(() => {
  "use strict";
  const lab = window.ROS2Lab;
  const $ = (id) => document.getElementById(id);
  const order = Object.keys(lab.chapters);
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const state = {
    chapter: "nodes",
    time: 0,
    playing: !reducedMotion,
    speed: 1,
    options: lab.defaultOptions(),
    selected: null,
    top: false,
  };
  const nodeButtons = {};
  let lastUI = -1,
    lastAnnouncement = "",
    scene;
  const formatTime = (t) => `00:${String(Math.floor(t)).padStart(2, "0")}`;
  const number = (n, places = 2) => (n === null ? "—" : n.toFixed(places));
  const text = (id, value) => {
    const e = $(id);
    if (e && e.textContent !== String(value)) e.textContent = value;
  };
  const kv = (label, id, initial = "—") =>
    `<div class="kv"><span>${label}</span><b id="${id}">${initial}</b></div>`;
  const phases = {
    SENDING: "发送目标",
    ACCEPTED: "目标已接受",
    EXECUTING: "执行中",
    CANCEL_REQUESTED: "取消请求在途",
    CANCELING: "取消已接受",
    SUCCEEDED: "服务端已成功",
    CANCELED: "服务端已取消",
    ABORTED: "服务端已中止",
  };

  for (const n of lab.nodes) {
    const button = document.createElement("button");
    button.className = "node-label";
    button.style.setProperty("--node-color", n.color);
    button.innerHTML = `<strong>${n.name}</strong><small>${n.role}</small>`;
    button.setAttribute("aria-label", `${n.name}：${n.role}，点击查看职责`);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () =>
      selectNode(state.selected === n.id ? null : n.id),
    );
    $("node-labels").appendChild(button);
    nodeButtons[n.id] = button;
  }
  const packetTags = Array.from({ length: 20 }, () => {
    const el = document.createElement("span");
    el.className = "packet-tag";
    el.hidden = true;
    $("packet-labels").appendChild(el);
    return el;
  });

  function selectNode(id) {
    state.selected = id;
    const n = lab.nodes.find((n) => n.id === id);
    text("detail-title", n ? n.name : "四个节点，一张通信图");
    text(
      "detail-copy",
      n ? n.detail : "点击节点，查看它负责什么。拖动画面可调整视角。",
    );
    $("detail-close").hidden = !n;
    for (const node of lab.nodes) {
      nodeButtons[node.id].classList.toggle("is-selected", node.id === id);
      nodeButtons[node.id].setAttribute("aria-pressed", String(node.id === id));
    }
  }
  $("detail-close").addEventListener("click", () => selectNode(null));

  function setupInspector() {
    const chapter = state.chapter;
    const body = $("inspector-body"),
      controls = $("experiment-controls");
    controls.innerHTML = "";
    if (chapter === "nodes") {
      text("inspector-title", "HOW THE GRAPH IS ORGANIZED");
      body.innerHTML =
        kv("battery_node", "node-battery", "电量发布者") +
        kv("pose_node", "node-pose", "二维位置积分") +
        kv("task_manager_node", "node-task", "缓存 / 服务 / 动作") +
        kv("command", "node-command", "服务 / 动作客户端") +
        '<p class="code-line">Workspace → Package → Executable<br>一个进程可创建一个或多个 Node</p>';
    } else if (chapter === "topic") {
      text("inspector-title", "std_msgs/msg/Int32");
      body.innerHTML =
        '<p class="interface-name">/lesson1/battery_level</p><p class="big-readout" id="topic-value">100<small>发布端 data</small></p>' +
        kv("task.battery_", "cache-value") +
        kv("距最近收到", "cache-age") +
        kv("publish_period_s", "topic-period", "0.2 s") +
        '<p class="code-line">create_publisher&lt;Int32&gt;("battery_level", 10)</p><p class="tiny-note">本演示可设 drain_per_tick=1，先发布再递减。源码默认 0，电量保持 100。</p>';
      controls.innerHTML =
        '<label class="drain-control">每次发布后的电量递减<select id="drain"><option value="1">1（观察变化）</option><option value="0">0（源码默认）</option></select></label><button class="experiment-button primary" id="next-message">停在下一条消息到达后 →</button>';
      $("drain").value = String(state.options.drain);
      $("drain").addEventListener("change", (e) => {
        state.options.drain = Number(e.target.value);
        lastUI = -1;
      });
      $("next-message").addEventListener("click", () => {
        const next = Math.floor(state.time - 1.65 + 1e-6) + 1 + 1.65;
        state.time = Math.min(14, Math.max(1.65, next) + 0.01);
        state.playing = false;
        lastUI = -1;
        syncControls();
      });
    } else if (chapter === "service") {
      text("inspector-title", "GetRobotStatus.Response");
      body.innerHTML =
        '<p class="interface-name">/lesson1/get_robot_status</p>' +
        kv("当前缓存年龄", "live-age") +
        '<div class="divider"></div>' +
        kv("收到第几次响应", "query-number") +
        kv("battery_level", "response-battery") +
        kv("valid", "response-valid") +
        kv("battery_age_s", "response-age") +
        kv("pose_age_s", "response-pose-age") +
        kv("has_task", "response-task") +
        '<p class="tiny-note" id="response-note">等待首次响应。年龄字段在服务端处理请求时取值。</p><p class="code-line">async_send_request(request, callback)<br>请求体为空：{}</p>';
      controls.innerHTML =
        '<button class="experiment-button primary" id="query-stale">跳到第二次查询 →</button>';
      $("query-stale").addEventListener("click", () => {
        state.time = 6;
        state.playing = true;
        lastUI = -1;
        syncControls();
      });
    } else if (chapter === "action") {
      text("inspector-title", "Navigation / Feedback → Result");
      body.innerHTML =
        '<p class="interface-name">/lesson1/navigation</p><p class="big-readout"><span id="distance">1.118</span><small>m 剩余距离</small></p><div class="mini-progress"><i id="distance-progress" style="width:0"></i></div>' +
        kv("current_x / y", "current-position") +
        kv("cmd_vel x / y", "current-velocity") +
        kv("服务端状态", "action-phase") +
        kv("客户端最终结果", "action-result") +
        '<p class="tiny-note" id="action-note">accepted 仅代表愿意执行，还不是成功。</p><p class="code-line">到达条件：distance ≤ 0.03 m<br>v = min(2, 0.5 / distance) × position_error</p>';
      controls.innerHTML =
        '<button class="experiment-button danger" id="cancel-goal">发送取消请求</button><button class="experiment-button" id="drop-pose">断开位置更新</button>';
      $("cancel-goal").addEventListener("click", () => {
        state.options.cancelAt = state.time;
        state.playing = true;
        lastUI = -1;
        syncControls();
      });
      $("drop-pose").addEventListener("click", () => {
        state.options.dropoutAt = state.time;
        state.playing = true;
        lastUI = -1;
        syncControls();
      });
    } else {
      text("inspector-title", "INPUT → BUSINESS CHECK");
      body.innerHTML =
        '<p class="code-line" id="contract-type" style="border:0;margin:0;padding:0"></p>' +
        kv("本条数据", "contract-input") +
        kv("业务要求", "contract-rule") +
        '<div class="divider"></div>' +
        kv("字段类型", "type-check") +
        kv("消息传输", "transport-check") +
        kv("业务检查", "business-check") +
        kv("task.battery_", "contract-cache") +
        '<p class="tiny-note" id="contract-note"></p>';
      controls.innerHTML =
        '<button class="experiment-button" data-scenario="range">电量 150</button><button class="experiment-button" data-scenario="frame">错误坐标系</button><button class="experiment-button" data-scenario="stamp">旧时间戳</button><button class="experiment-button" data-scenario="valid">合法电量 99</button>';
      controls.querySelectorAll("[data-scenario]").forEach((button) => {
        button.setAttribute(
          "aria-pressed",
          String(button.dataset.scenario === state.options.scenario),
        );
        button.addEventListener("click", () => {
          state.options.scenario = button.dataset.scenario;
          state.time = 0;
          state.playing = true;
          lastUI = -1;
          setupInspector();
          syncControls();
        });
      });
    }
  }

  function enterChapter(id) {
    state.chapter = id;
    state.time = 0;
    state.options = lab.defaultOptions();
    state.playing = !reducedMotion;
    lastUI = -1;
    lastAnnouncement = "";
    const c = lab.chapters[id];
    document.querySelectorAll("[data-chapter]").forEach((b) => {
      b.classList.toggle("active", b.dataset.chapter === id);
      if (b.dataset.chapter === id) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    text("panel-number", `${c.number} / 04`);
    text("panel-kind", c.kind);
    $("lesson-title").innerHTML = c.title;
    text("lesson-description", c.description);
    $("steps").innerHTML = c.steps
      .map(
        (s, i) =>
          `<li><span>${i + 1}</span><div><b>${s[1]}</b><small>${s[2]}</small></div></li>`,
      )
      .join("");
    $("takeaway").innerHTML = c.takeaway;
    text("timeline-label", c.label);
    $("next-chapter").innerHTML = `${c.next} <span aria-hidden="true">→</span>`;
    $("timeline").max = String(c.duration);
    $("map-inset").hidden = id !== "action";
    $("stage").classList.toggle("has-map", id === "action");
    selectNode(null);
    setupInspector();
    syncControls();
  }

  function syncControls() {
    text(
      "play-icon",
      state.playing
        ? "Ⅱ"
        : state.time >= lab.chapters[state.chapter].duration
          ? "↺"
          : "▶",
    );
    $("play").setAttribute(
      "aria-label",
      state.playing
        ? "暂停演示"
        : state.time >= lab.chapters[state.chapter].duration
          ? "重新播放本章"
          : "播放演示",
    );
  }
  function togglePlay() {
    if (state.time >= lab.chapters[state.chapter].duration) state.time = 0;
    state.playing = !state.playing;
    syncControls();
  }

  function updateInspector(s) {
    const status = $("inspector-status");
    status.className = "status-pill";
    if (s.chapter === "nodes")
      text("inspector-status", s.t < 7 ? "分工" : "连接");
    if (s.chapter === "topic") {
      $("topic-value").firstChild.nodeValue = String(s.battery);
      text("cache-value", s.cache === null ? "等待消息" : s.cache);
      text(
        "cache-age",
        s.cacheAge === null ? "—" : `${number(s.cacheAge, 3)} s`,
      );
      text("inspector-status", s.cache === null ? "等待订阅回调" : "持续更新");
      $("next-message").disabled = s.t >= 13.65;
    }
    if (s.chapter === "service") {
      text(
        "live-age",
        s.cacheAge === null
          ? "尚未收到状态"
          : `${number(s.cacheAge, 3)} s${s.cacheAge > 0.8 ? " · 已过期" : ""}`,
      );
      $("live-age").classList.toggle("bad", s.cacheAge > 0.8);
      const r = s.response;
      text("query-number", r ? r.query : "—");
      text("response-battery", r ? r.battery : "—");
      text("response-valid", r ? String(r.valid) : "—");
      text("response-age", r ? `${number(r.age, 3)} s` : "—");
      text("response-pose-age", r ? `${number(r.age, 3)} s` : "—");
      text("response-task", r ? "false" : "—");
      $("response-valid").classList.toggle("bad", Boolean(r && !r.valid));
      text(
        "inspector-status",
        s.queryPending ? "请求处理中" : r ? `快照 ${r.query}` : "等待响应",
      );
      status.classList.toggle("bad", Boolean(r && !r.valid));
      status.classList.toggle("blue", s.queryPending);
      text(
        "response-note",
        r
          ? `第 ${r.query} 次响应在演示 ${r.query === 1 ? "2.7" : "6.7"} s 读取缓存，年龄 ${number(r.age, 2)} s。响应字段保持这次查询的值。`
          : "等待首次响应。年龄字段在服务端处理请求时取值。",
      );
      $("query-stale").disabled = s.t >= 6;
    }
    if (s.chapter === "action") {
      const m = s.motion;
      text("distance", number(m.distance, 3));
      text(
        "current-position",
        `${number(m.lastPoseX)} / ${number(m.lastPoseY)} m`,
      );
      text("current-velocity", `${number(m.vx)} / ${number(m.vy)} m/s`);
      text("action-phase", phases[m.phase]);
      text("action-result", s.resultReceived ? m.phase : "尚未收到");
      $("action-result").classList.toggle(
        "bad",
        s.resultReceived && m.phase !== "SUCCEEDED",
      );
      $("distance-progress").style.width =
        `${Math.max(0, 1 - m.distance / Math.hypot(1, 0.5)) * 100}%`;
      text(
        "inspector-status",
        s.resultReceived
          ? m.phase
          : m.terminalAt !== null
            ? "结果传输中"
            : m.phase,
      );
      status.classList.toggle("bad", ["ABORTED", "CANCELED"].includes(m.phase));
      const running = ["EXECUTING"].includes(m.phase);
      $("cancel-goal").disabled = !running || state.options.cancelAt !== null;
      $("drop-pose").disabled = !running || state.options.dropoutAt !== null;
      text(
        "cancel-goal",
        state.options.cancelAt === null ? "发送取消请求" : "取消请求已发出",
      );
      text(
        "drop-pose",
        state.options.dropoutAt === null ? "断开位置更新" : "位置更新已断开",
      );
      let note = "accepted 仅代表愿意执行，还不是成功。";
      if (m.phase === "EXECUTING")
        note =
          "Feedback.distance_remaining 是最近观测的距离。这里是二维运动学示意。";
      if (
        state.options.dropoutAt !== null &&
        s.t >= state.options.dropoutAt &&
        m.terminalAt === null
      )
        note = "位置消息已停止；仍使用最后观测值，状态年龄超过 0.8 s 后中止。";
      if (m.phase === "CANCEL_REQUESTED")
        note = "取消请求正在传输，服务端仍可能继续执行。";
      if (m.phase === "CANCELING")
        note = "服务端接受取消，等待停止执行与终止结果。";
      if (m.terminalAt !== null)
        note = `已发布零速度；${s.resultReceived ? "客户端收到" : "等待客户端收到"} ${m.phase}。final_distance=${number(m.terminalDistance, 3)} m（最后观测值）。`;
      text("action-note", note);
      drawMap(m);
    }
    if (s.chapter === "contracts") {
      const c = s.contract,
        arrived = s.t >= 2,
        checked = s.t >= 3;
      text("contract-type", c.type);
      text("contract-input", c.input);
      text("contract-rule", c.rule);
      text("type-check", "通过");
      text("transport-check", arrived ? "已到达回调" : "在途 / 待发送");
      text("business-check", checked ? c.reason : "等待检查");
      text("contract-cache", s.cache);
      $("business-check").classList.toggle("bad", checked && !c.accepted);
      text(
        "contract-note",
        checked
          ? c.accepted
            ? "回调接收新值，缓存由 100 更新为 99。"
            : "本条输入被丢弃，之前缓存不变；位置示例中电量缓存同样保持 100。"
          : "本例初始缓存电量为 100。观察输入到达后，缓存是否变化。",
      );
      text(
        "inspector-status",
        checked
          ? c.accepted
            ? "接收"
            : "丢弃"
          : arrived
            ? "回调检查中"
            : "等待到达",
      );
      status.classList.toggle("bad", checked && !c.accepted);
    }
  }

  function drawMap(m) {
    const canvas = $("motion-map"),
      ctx = canvas.getContext("2d");
    const w = canvas.clientWidth,
      h = canvas.clientHeight,
      dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (
      canvas.width !== Math.round(w * dpr) ||
      canvas.height !== Math.round(h * dpr)
    ) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const left = 18,
      bottom = h - 18,
      sx = (w - 38) / 1.25,
      sy = (h - 25) / 0.8;
    const p = (x, y) => [left + x * sx, bottom - y * sy];
    ctx.strokeStyle = "#749a8a33";
    ctx.lineWidth = 0.6;
    for (let x = 0; x <= 1.25; x += 0.25) {
      ctx.beginPath();
      ctx.moveTo(...p(x, 0));
      ctx.lineTo(...p(x, 0.7));
      ctx.stroke();
    }
    for (let y = 0; y <= 0.7; y += 0.25) {
      ctx.beginPath();
      ctx.moveTo(...p(0, y));
      ctx.lineTo(...p(1.2, y));
      ctx.stroke();
    }
    ctx.font = "7px monospace";
    ctx.fillStyle = "#92ad9f";
    ctx.fillText("0", 7, bottom + 3);
    ctx.fillText("1.0 x", ...p(0.96, -0.13));
    ctx.fillText("y", 4, 12);
    const target = p(1, 0.5);
    ctx.strokeStyle = "#e6bd7d";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(...target, 6, 0, Math.PI * 2);
    ctx.moveTo(target[0] - 9, target[1]);
    ctx.lineTo(target[0] + 9, target[1]);
    ctx.moveTo(target[0], target[1] - 9);
    ctx.lineTo(target[0], target[1] + 9);
    ctx.stroke();
    ctx.strokeStyle = "#9bbf9a";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    m.trail.forEach((v, i) => {
      const q = p(...v);
      if (i) ctx.lineTo(...q);
      else ctx.moveTo(...q);
    });
    ctx.stroke();
    const current = p(m.x, m.y);
    ctx.fillStyle = "#c4ddaf";
    ctx.beginPath();
    ctx.arc(...current, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  function render(timestamp) {
    const delta =
      lastFrame === null ? 0 : Math.min((timestamp - lastFrame) / 1000, 0.1);
    lastFrame = timestamp;
    if (state.playing) {
      state.time = Math.min(
        state.time + delta * state.speed,
        lab.chapters[state.chapter].duration,
      );
      if (state.time >= lab.chapters[state.chapter].duration) {
        state.playing = false;
        syncControls();
      }
    }
    const s = lab.sample(state.chapter, state.time, state.options);
    scene.draw(s);
    for (const n of lab.nodes) {
      const point = scene.node(n.id),
        el = nodeButtons[n.id];
      const half = el.offsetWidth / 2 + 4;
      el.style.left = `${Math.max(half, Math.min($("stage").clientWidth - half, point.x))}px`;
      el.style.top = `${Math.max(89, Math.min($("stage").clientHeight - 111, point.y))}px`;
      el.classList.toggle("is-dim", !s.focus.includes(n.id));
      el.classList.toggle(
        "is-pulsing",
        s.packets.some((p) => {
          const e = lab.edges.find((e) => e.id === p.edge);
          return (
            (e.from === n.id && p.progress < 0.3) ||
            (e.to === n.id && p.progress > 0.7)
          );
        }),
      );
    }
    packetTags.forEach((el, i) => {
      const p = s.packets[i];
      // 每一方向至多显示一个文字标签，避免多条消息文字叠在一起。
      const visible =
        p && !s.packets.slice(0, i).some((q) => q.edge === p.edge);
      el.hidden = !visible;
      if (visible) {
        const point = scene.packet(p);
        el.style.left = `${point.x}px`;
        el.style.top = `${point.y}px`;
        el.style.color = lab.colors[p.kind];
        el.textContent = p.label;
      }
    });
    if (lastUI < 0 || timestamp - lastUI >= 75) {
      lastUI = timestamp;
      updateInspector(s);
      $("timeline").value = String(state.time);
      $("timeline").style.setProperty(
        "--progress",
        `${(state.time / lab.chapters[state.chapter].duration) * 100}%`,
      );
      const timeText = `${formatTime(state.time)} / ${formatTime(lab.chapters[state.chapter].duration)}`;
      text("time-label", timeText);
      $("timeline").setAttribute(
        "aria-valuetext",
        `${number(state.time, 1)} 秒，共 ${lab.chapters[state.chapter].duration} 秒演示时间`,
      );
      [...$("steps").children].forEach((li, i) => {
        li.classList.toggle("current", i === s.stage);
        li.classList.toggle("done", i < s.stage);
        if (i === s.stage) li.setAttribute("aria-current", "step");
        else li.removeAttribute("aria-current");
      });
      const announcement = `${state.chapter}/${s.stage}/${s.motion?.phase ?? ""}/${s.response?.query ?? ""}`;
      if (announcement !== lastAnnouncement) {
        lastAnnouncement = announcement;
        text(
          "announcement",
          `${lab.chapters[state.chapter].steps[s.stage][1]}${s.motion ? `；${phases[s.motion.phase]}` : ""}`,
        );
      }
    }
    requestAnimationFrame(render);
  }

  document
    .querySelectorAll("[data-chapter]")
    .forEach((b) =>
      b.addEventListener("click", () => enterChapter(b.dataset.chapter)),
    );
  $("next-chapter").addEventListener("click", () =>
    enterChapter(order[(order.indexOf(state.chapter) + 1) % order.length]),
  );
  $("play").addEventListener("click", togglePlay);
  $("replay").addEventListener("click", () => {
    state.time = 0;
    state.options.cancelAt = null;
    state.options.dropoutAt = null;
    state.playing = !reducedMotion;
    lastUI = -1;
    syncControls();
  });
  $("timeline").addEventListener("input", (e) => {
    state.time = Number(e.target.value);
    state.playing = false;
    lastUI = -1;
    syncControls();
  });
  $("speed").addEventListener("change", (e) => {
    state.speed = Number(e.target.value);
  });
  $("camera-reset").addEventListener("click", () => {
    scene.reset();
    state.top = false;
    $("camera-top").setAttribute("aria-pressed", "false");
  });
  $("camera-top").addEventListener("click", () => {
    state.top = !state.top;
    scene.top(state.top);
    $("camera-top").setAttribute("aria-pressed", String(state.top));
  });
  window.addEventListener("keydown", (e) => {
    if (!["BODY", "CANVAS"].includes(document.activeElement.tagName)) return;
    if (e.code === "Space") {
      e.preventDefault();
      togglePlay();
    }
    if (e.code === "ArrowRight" || e.code === "ArrowLeft") {
      e.preventDefault();
      state.time = Math.max(
        0,
        Math.min(
          lab.chapters[state.chapter].duration,
          state.time + (e.code === "ArrowRight" ? 0.25 : -0.25),
        ),
      );
      state.playing = false;
      lastUI = -1;
      syncControls();
    }
  });
  window.addEventListener("resize", () => scene.resize());
  window.addEventListener("visibilitychange", () => {
    lastFrame = null;
  });
  window.addEventListener("ros2-context-lost", () => {
    const old = $("scene"),
      replacement = old.cloneNode(false);
    scene.dispose();
    old.replaceWith(replacement);
    scene = lab.fallbackScene(replacement);
    text("renderer-status", scene.mode);
  });
  scene = lab.startScene($("scene"), (upgraded) => {
    scene = upgraded;
    scene.top(state.top);
    text("renderer-status", scene.mode);
  });
  text("renderer-status", scene.mode);
  enterChapter("nodes");
  let lastFrame = null;
  requestAnimationFrame(render);
})();
