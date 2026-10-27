/* 同一组节点 / 曲线驱动 Three.js 和离线 Canvas 两种画面。 */
(() => {
  "use strict";
  const lab = window.ROS2Lab;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const nodeById = Object.fromEntries(lab.nodes.map((n) => [n.id, n]));
  const edgeById = Object.fromEntries(lab.edges.map((e) => [e.id, e]));

  function curvePoints(edge) {
    const a = nodeById[edge.from].position;
    const b = nodeById[edge.to].position;
    const dx = b[0] - a[0],
      dz = b[2] - a[2];
    return [
      [a[0], 0.65, a[2]],
      [
        a[0] + dx * 0.34 - dz * edge.bend * 0.3,
        edge.lift + 0.6,
        a[2] + dz * 0.34 + dx * edge.bend * 0.3,
      ],
      [
        a[0] + dx * 0.7 - dz * edge.bend * 0.3,
        edge.lift + 0.6,
        a[2] + dz * 0.7 + dx * edge.bend * 0.3,
      ],
      [b[0], 0.65, b[2]],
    ];
  }
  function curveAt(edge, t) {
    const p = curvePoints(edge),
      u = 1 - t;
    return [0, 1, 2].map(
      (i) =>
        u ** 3 * p[0][i] +
        3 * u ** 2 * t * p[1][i] +
        3 * u * t ** 2 * p[2][i] +
        t ** 3 * p[3][i],
    );
  }

  function bindCamera(canvas, view) {
    let start = null;
    const down = (e) => {
      if (e.button === 0)
        start = {
          x: e.clientX,
          y: e.clientY,
          yaw: view.yaw,
          elevation: view.elevation,
        };
    };
    const move = (e) => {
      if (!start) return;
      const dx = e.clientX - start.x,
        dy = e.clientY - start.y;
      if (
        e.pointerType === "touch" &&
        Math.abs(dy) > Math.abs(dx) &&
        !canvas.hasPointerCapture(e.pointerId)
      ) {
        start = null;
        return;
      }
      if (Math.hypot(dx, dy) > 5) canvas.setPointerCapture(e.pointerId);
      view.yaw = clamp(start.yaw - dx * 0.004, -0.8, 0.95);
      view.elevation = clamp(start.elevation + dy * 0.003, 0.45, 1.5);
    };
    const up = () => {
      start = null;
    };
    const wheel = (e) => {
      e.preventDefault();
      view.zoom = clamp(view.zoom * Math.exp(-e.deltaY * 0.0006), 0.8, 1.4);
    };
    canvas.addEventListener("pointerdown", down);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
    canvas.addEventListener("lostpointercapture", up);
    canvas.addEventListener("wheel", wheel, { passive: false });
    return () => {
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", up);
      canvas.removeEventListener("lostpointercapture", up);
      canvas.removeEventListener("wheel", wheel);
    };
  }
  function makeView() {
    return { yaw: 0.32, elevation: 0.7, zoom: 1 };
  }
  function reset(view) {
    Object.assign(view, makeView());
  }

  function canvasScene(canvas) {
    const ctx = canvas.getContext("2d");
    const view = makeView(),
      unbind = bindCamera(canvas, view);
    let width = 1,
      height = 1,
      scale = 1;
    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function project(point) {
      const [x, y, z] = point,
        c = Math.cos(view.yaw),
        s = Math.sin(view.yaw);
      return {
        x: width * 0.5 + (x * c - z * s) * scale,
        y:
          height * 0.44 +
          ((x * s + z * c) * Math.sin(view.elevation) -
            y * Math.cos(view.elevation)) *
            scale,
      };
    }
    function path(points, stroke, fill, lineWidth = 1) {
      ctx.beginPath();
      points.forEach((p, i) => {
        const v = project(p);
        if (i) ctx.lineTo(v.x, v.y);
        else ctx.moveTo(v.x, v.y);
      });
      if (fill) {
        ctx.closePath();
        ctx.fillStyle = fill;
        ctx.fill();
      }
      if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
      }
    }
    function ring(x, y, z, r, color) {
      path(
        Array.from({ length: 65 }, (_, i) => [
          x + Math.cos((i / 64) * Math.PI * 2) * r,
          y,
          z + Math.sin((i / 64) * Math.PI * 2) * r,
        ]),
        color,
        null,
      );
    }
    function box(x, y, z, w, h, d, top, side, front) {
      const a = x - w / 2,
        b = x + w / 2,
        c = z - d / 2,
        f = z + d / 2;
      path(
        [
          [a, y, c],
          [b, y, c],
          [b, y, f],
          [a, y, f],
        ],
        "#bfd0b722",
        side,
      );
      path(
        [
          [a, y, c],
          [a, y + h, c],
          [a, y + h, f],
          [a, y, f],
        ],
        "#b6c7b71c",
        side,
      );
      path(
        [
          [a, y, f],
          [b, y, f],
          [b, y + h, f],
          [a, y + h, f],
        ],
        "#bfd0b722",
        front,
      );
      path(
        [
          [b, y, c],
          [b, y + h, c],
          [b, y + h, f],
          [b, y, f],
        ],
        "#bfd0b722",
        side,
      );
      path(
        [
          [a, y + h, c],
          [b, y + h, c],
          [b, y + h, f],
          [a, y + h, f],
        ],
        "#d6dec935",
        top,
      );
    }
    function draw(state) {
      scale =
        Math.min(width / (width < 420 ? 12.4 : 13.6), height / 9) * view.zoom;
      ctx.clearRect(0, 0, width, height);
      for (let i = -10; i <= 10; i++) {
        path(
          [
            [i, -0.14, -8],
            [i, -0.14, 8],
          ],
          "#78938b13",
        );
        path(
          [
            [-10, -0.14, i],
            [10, -0.14, i],
          ],
          "#78938b13",
        );
      }
      ring(0, -0.1, 0, 5.9, "#73978a20");
      for (const e of lab.edges) {
        ctx.globalAlpha = state.activeEdges.includes(e.id) ? 0.6 : 0.1;
        path(
          Array.from({ length: 42 }, (_, i) => curveAt(e, i / 41)),
          lab.colors[e.kind],
          null,
          1.3,
        );
        const tip = project(curveAt(e, 0.8)),
          prev = project(curveAt(e, 0.78));
        const angle = Math.atan2(tip.y - prev.y, tip.x - prev.x);
        ctx.beginPath();
        ctx.moveTo(tip.x, tip.y);
        ctx.lineTo(
          tip.x - 7 * Math.cos(angle - 0.45),
          tip.y - 7 * Math.sin(angle - 0.45),
        );
        ctx.lineTo(
          tip.x - 7 * Math.cos(angle + 0.45),
          tip.y - 7 * Math.sin(angle + 0.45),
        );
        ctx.closePath();
        ctx.fillStyle = lab.colors[e.kind];
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      const sorted = [...lab.nodes].sort(
        (a, b) =>
          (a.position[0] - b.position[0]) * Math.sin(view.yaw) +
          (a.position[2] - b.position[2]) * Math.cos(view.yaw),
      );
      for (const n of sorted) {
        const [x, , z] = n.position;
        ctx.globalAlpha = state.focus.includes(n.id) ? 1 : 0.36;
        ring(x, -0.1, z, 1.28, "#afc4ac44");
        box(x, 0, z, 1.85, 0.2, 1.5, "#627b6e", "#2e4845", "#3b5650");
        if (n.id === "battery") {
          for (const off of [-0.44, 0, 0.44]) {
            box(
              x + off,
              0.2,
              z,
              0.31,
              0.8,
              0.5,
              "#f0c596",
              "#9e744e",
              "#c19a6b",
            );
            box(
              x + off,
              1,
              z,
              0.13,
              0.09,
              0.24,
              "#e7dcaf",
              "#b6b290",
              "#b6b290",
            );
          }
        } else if (n.id === "task") {
          for (let i = 0; i < 3; i++) {
            box(
              x,
              0.23 + i * 0.3,
              z,
              1.2,
              0.23,
              0.95,
              "#a1b594",
              "#5b7863",
              "#789576",
            );
            box(
              x + 0.36,
              0.3 + i * 0.3,
              z + 0.49,
              0.12,
              0.055,
              0.015,
              "#d4e7ac",
              "#d4e7ac",
              "#d4e7ac",
            );
          }
        } else if (n.id === "pose") {
          box(x, 0.22, z, 1.1, 0.29, 0.83, "#d2d7bc", "#728b7b", "#9bae94");
          box(
            x,
            0.51,
            z - 0.12,
            0.65,
            0.25,
            0.47,
            "#d7dfc5",
            "#7f9a84",
            "#adbea1",
          );
          for (const off of [-0.6, 0.6])
            box(
              x + off,
              0.21,
              z,
              0.18,
              0.25,
              0.65,
              "#364e49",
              "#253c38",
              "#253c38",
            );
          ring(x, 0.79, z - 0.1, 0.14, "#f2bc78");
        } else {
          box(x, 0.24, z, 0.13, 0.38, 0.15, "#b4c5ac", "#7e9681", "#7e9681");
          box(x, 0.54, z, 1.2, 0.72, 0.16, "#9cad9a", "#627c70", "#24403e");
          for (let i = 0; i < 3; i++)
            box(
              x - 0.12 + i * 0.04,
              0.72 + i * 0.14,
              z + 0.095,
              0.65 - i * 0.13,
              0.035,
              0.01,
              "#a2cbb5",
              "#a2cbb5",
              "#a2cbb5",
            );
        }
      }
      ctx.globalAlpha = 1;
      for (const p of state.packets) {
        const v = project(curveAt(edgeById[p.edge], p.progress));
        ctx.shadowBlur = 15;
        ctx.shadowColor = lab.colors[p.kind];
        ctx.fillStyle = lab.colors[p.kind];
        ctx.beginPath();
        ctx.arc(v.x, v.y, 3.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
    resize();
    return {
      mode: "CANVAS · 离线可用",
      draw,
      resize,
      reset: () => reset(view),
      top: (on) => {
        view.elevation = on ? 1.5 : 0.7;
      },
      node: (id) => {
        const p = nodeById[id].position;
        return project([p[0], 0.03, p[2] + 1]);
      },
      packet: (p) => project(curveAt(edgeById[p.edge], p.progress)),
      dispose: unbind,
    };
  }

  function threeScene(T, previousCanvas) {
    const canvas = previousCanvas.cloneNode(false);
    const renderer = new T.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = T.PCFSoftShadowMap;
    const scene = new T.Scene();
    scene.fog = new T.FogExp2("#14282d", 0.025);
    const camera = new T.OrthographicCamera(-7, 7, 5, -5, 0.1, 100);
    const view = makeView();
    const unbind = bindCamera(canvas, view);
    scene.add(new T.HemisphereLight("#f1f4de", "#1e4244", 2.8));
    const sun = new T.DirectionalLight("#fff1d8", 4.4);
    sun.position.set(-4, 11, 7);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1024, 1024);
    Object.assign(sun.shadow.camera, {
      left: -9,
      right: 9,
      top: 8,
      bottom: -8,
    });
    sun.shadow.normalBias = 0.04;
    scene.add(sun);
    const fill = new T.DirectionalLight("#8ab3b3", 2);
    fill.position.set(6, 5, -7);
    scene.add(fill);
    const floor = new T.Mesh(
      new T.PlaneGeometry(35, 35),
      new T.MeshStandardMaterial({
        color: "#233b3d",
        roughness: 1,
        transparent: true,
        opacity: 0.5,
      }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.17;
    floor.receiveShadow = true;
    scene.add(floor);
    const grid = new T.GridHelper(24, 48, "#638a7a", "#638a7a");
    grid.position.y = -0.15;
    grid.material.transparent = true;
    grid.material.opacity = 0.13;
    scene.add(grid);

    const materials = {};
    function material(color, metalness = 0.1) {
      const key = `${color}/${metalness}`;
      return (materials[key] ??= new T.MeshStandardMaterial({
        color,
        roughness: 0.5,
        metalness,
      }));
    }
    function roundedBox(w, h, d, r = 0.07) {
      const shape = new T.Shape();
      const x = -w / 2,
        y = -d / 2;
      shape.moveTo(x + r, y);
      shape.lineTo(x + w - r, y);
      shape.quadraticCurveTo(x + w, y, x + w, y + r);
      shape.lineTo(x + w, y + d - r);
      shape.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
      shape.lineTo(x + r, y + d);
      shape.quadraticCurveTo(x, y + d, x, y + d - r);
      shape.lineTo(x, y + r);
      shape.quadraticCurveTo(x, y, x + r, y);
      const geometry = new T.ExtrudeGeometry(shape, {
        depth: h,
        bevelEnabled: true,
        bevelSegments: 2,
        steps: 1,
        bevelSize: 0.025,
        bevelThickness: 0.025,
        curveSegments: 6,
      });
      geometry.rotateX(-Math.PI / 2);
      return geometry;
    }
    function box(group, w, h, d, color, x = 0, y = 0, z = 0) {
      const mesh = new T.Mesh(
        roundedBox(w, h, d, Math.min(0.07, w / 5, d / 5)),
        material(color),
      );
      mesh.position.set(x, y, z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      group.add(mesh);
      return mesh;
    }
    function cylinder(group, r, h, color, x, y, z) {
      const mesh = new T.Mesh(
        new T.CylinderGeometry(r, r, h, 32),
        material(color, 0.3),
      );
      mesh.position.set(x, y, z);
      mesh.castShadow = true;
      group.add(mesh);
      return mesh;
    }
    function torus(group, r, tube, color, y) {
      const mesh = new T.Mesh(
        new T.TorusGeometry(r, tube, 8, 80),
        new T.MeshBasicMaterial({ color, transparent: true, opacity: 0.35 }),
      );
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.y = y;
      group.add(mesh);
      return mesh;
    }
    const nodeObjects = {};
    for (const n of lab.nodes) {
      const group = new T.Group();
      group.position.fromArray(n.position);
      scene.add(group);
      const halo = torus(group, 1.25, 0.009, n.color, -0.12);
      box(group, 1.85, 0.18, 1.5, "#5c7666");
      box(group, 1.65, 0.025, 1.3, "#89977c", 0, 0.2);
      if (n.id === "battery") {
        for (const offset of [-0.43, 0, 0.43]) {
          cylinder(group, 0.17, 0.72, "#b88957", offset, 0.64, 0);
          cylinder(group, 0.173, 0.14, "#d8c094", offset, 0.98, 0);
          cylinder(group, 0.072, 0.055, "#e7ddba", offset, 1.08, 0);
          cylinder(group, 0.172, 0.05, "#344f49", offset, 0.3, 0);
        }
      } else if (n.id === "task") {
        for (let i = 0; i < 3; i++) {
          box(
            group,
            1.18,
            0.23,
            0.92,
            i === 2 ? "#b8c5a1" : "#9ead8e",
            0,
            0.25 + i * 0.31,
            0,
          );
          box(
            group,
            0.12,
            0.035,
            0.015,
            "#dfedb5",
            0.36,
            0.35 + i * 0.31,
            0.48,
          );
          box(
            group,
            0.45,
            0.018,
            0.018,
            "#5a7762",
            -0.17,
            0.35 + i * 0.31,
            0.48,
          );
        }
        torus(group, 0.21, 0.015, "#d6e0b5", 1.14);
      } else if (n.id === "pose") {
        box(group, 1.1, 0.27, 0.8, "#b8c8a6", 0, 0.36);
        box(group, 0.68, 0.22, 0.5, "#d8ddbd", 0, 0.64, -0.07);
        cylinder(group, 0.14, 0.1, "#415e53", 0, 0.91, -0.08);
        cylinder(group, 0.12, 0.035, "#f0bb78", 0, 0.98, -0.08);
        for (const x of [-0.59, 0.59])
          for (const z of [-0.25, 0.25]) {
            const wheel = new T.Mesh(
              new T.CylinderGeometry(0.19, 0.19, 0.13, 20),
              material("#243f3b"),
            );
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(x, 0.35, z);
            group.add(wheel);
          }
      } else {
        box(group, 0.59, 0.06, 0.4, "#a3b599", 0, 0.24);
        box(group, 0.12, 0.4, 0.12, "#819a84", 0, 0.3, -0.03);
        box(group, 1.18, 0.75, 0.13, "#b2bda2", 0, 0.64, -0.03);
        box(group, 1.04, 0.61, 0.02, "#264441", 0, 0.72, 0.055);
        box(group, 0.12, 0.035, 0.02, "#9cd2b9", -0.33, 1.16, 0.08);
        for (let i = 0; i < 3; i++)
          box(
            group,
            0.53 - i * 0.08,
            0.024,
            0.02,
            "#9cbaaa",
            -0.1 + i * 0.04,
            1.03 - i * 0.1,
            0.08,
          );
      }
      nodeObjects[n.id] = { group, halo };
    }

    const curves = {},
      links = {};
    for (const e of lab.edges) {
      const points = curvePoints(e).map((p) => new T.Vector3(...p));
      const curve = new T.CubicBezierCurve3(...points);
      curves[e.id] = curve;
      const tube = new T.Mesh(
        new T.TubeGeometry(curve, 48, 0.012, 5, false),
        new T.MeshBasicMaterial({
          color: lab.colors[e.kind],
          transparent: true,
          opacity: 0.45,
          depthWrite: false,
        }),
      );
      scene.add(tube);
      links[e.id] = tube;
      // 箭头永远指向接收端，不用运动方向猜测通信方向。
      const arrow = new T.Mesh(
        new T.ConeGeometry(0.065, 0.19, 10),
        new T.MeshBasicMaterial({
          color: lab.colors[e.kind],
          transparent: true,
          opacity: 0.7,
        }),
      );
      arrow.position.copy(curve.getPoint(0.8));
      arrow.quaternion.setFromUnitVectors(
        new T.Vector3(0, 1, 0),
        curve.getTangent(0.8).normalize(),
      );
      scene.add(arrow);
      links[e.id].userData.arrow = arrow;
    }
    const spheres = Array.from({ length: 20 }, () => {
      const mesh = new T.Mesh(
        new T.SphereGeometry(0.055, 12, 10),
        new T.MeshBasicMaterial({ color: "white" }),
      );
      scene.add(mesh);
      mesh.visible = false;
      return mesh;
    });
    let width = 1,
      height = 1;
    const projected = new T.Vector3();
    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
    }
    function draw(state) {
      const aspect = width / height;
      const halfHeight =
        Math.max(4.5, (width < 420 ? 6.2 : 6.8) / aspect) / view.zoom;
      camera.left = -halfHeight * aspect;
      camera.right = halfHeight * aspect;
      camera.top = halfHeight;
      camera.bottom = -halfHeight;
      camera.position.set(
        Math.sin(view.yaw) * 18 * Math.cos(view.elevation),
        18 * Math.sin(view.elevation),
        Math.cos(view.yaw) * 18 * Math.cos(view.elevation),
      );
      camera.lookAt(0, 0.1, 0.3);
      camera.updateProjectionMatrix();
      camera.updateMatrixWorld();
      for (const n of lab.nodes) {
        const active = state.focus.includes(n.id);
        nodeObjects[n.id].halo.material.opacity = active ? 0.65 : 0.12;
        nodeObjects[n.id].group.position.y = 0;
      }
      for (const e of lab.edges) {
        const active = state.activeEdges.includes(e.id);
        links[e.id].material.opacity = active ? 0.48 : 0.045;
        links[e.id].userData.arrow.material.opacity = active ? 0.75 : 0.06;
      }
      spheres.forEach((mesh, i) => {
        const p = state.packets[i];
        mesh.visible = Boolean(p);
        if (p) {
          mesh.position.copy(curves[p.edge].getPoint(p.progress));
          mesh.material.color.set(lab.colors[p.kind]);
          mesh.scale.setScalar(1 + Math.sin(p.progress * Math.PI) * 0.45);
        }
      });
      renderer.render(scene, camera);
    }
    function project(p) {
      projected.set(...p).project(camera);
      return {
        x: ((projected.x + 1) / 2) * width,
        y: ((1 - projected.y) / 2) * height,
      };
    }
    previousCanvas.replaceWith(canvas);
    resize();
    canvas.addEventListener("webglcontextlost", (e) => {
      e.preventDefault();
      window.dispatchEvent(new Event("ros2-context-lost"));
    });
    return {
      mode: "THREE.JS · 3D",
      draw,
      resize,
      reset: () => reset(view),
      top: (on) => {
        view.elevation = on ? 1.5 : 0.7;
      },
      node: (id) => {
        const p = nodeById[id].position;
        return project([p[0], 0.02, p[2] + 1]);
      },
      packet: (p) => {
        const v = curves[p.edge].getPoint(p.progress);
        return project([v.x, v.y, v.z]);
      },
      dispose: () => {
        unbind();
        scene.traverse((o) => {
          o.geometry?.dispose();
          if (o.material) {
            for (const m of Array.isArray(o.material)
              ? o.material
              : [o.material])
              m.dispose();
          }
        });
        renderer.dispose();
      },
    };
  }

  lab.startScene = (canvas, onUpgrade) => {
    const fallback = canvasScene(canvas);
    // CDN 依赖不阻塞页面；失败时保留完整的离线交互。
    import("https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js")
      .then((T) => {
        try {
          const upgraded = threeScene(T, canvas);
          fallback.dispose();
          onUpgrade(upgraded);
        } catch (error) {
          console.info("Three.js 不可用，保留 Canvas 画面。", error.message);
        }
      })
      .catch(() => {
        /* 离线时维持 Canvas，无需弹窗。 */
      });
    return fallback;
  };
  lab.fallbackScene = canvasScene;
})();
