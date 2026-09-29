"""第六章单关节闭环案例。只运行仓库 MuJoCo 模型，不连接硬件。"""

from dataclasses import asdict, dataclass
from pathlib import Path
import argparse
import json
import math
import platform
import random

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent / '04_forward_inverse_dynamics/single_rod.xml'
INERTIA, DAMPING, GRAVITY = .24, .2, 5.886
LIMIT = 4.0


def clip(value, bound=LIMIT):
    return max(-bound, min(bound, value))


def quintic(t, duration=2.0, goal=.5):
    """位置 rad，速度 rad/s，加速度 rad/s²；起止速度、加速度均为零。"""
    if t <= 0:
        return 0.0, 0.0, 0.0
    if t >= duration:
        return goal, 0.0, 0.0
    s = t / duration
    return (goal * (10*s**3 - 15*s**4 + 6*s**5),
            goal / duration * (30*s**2 - 60*s**3 + 30*s**4),
            goal / duration**2 * (60*s - 180*s**2 + 120*s**3))


def peaks(duration, goal):
    return 1.875 * abs(goal) / duration, (10 * math.sqrt(3) / 3) * abs(goal) / duration**2


@dataclass(frozen=True)
class Case:
    name: str
    controller: str = 'ff_pd'
    reference: str = 'smooth'
    goal: float = .5
    move_time: float = 2.0
    end_time: float = 6.0
    kp: float = 12.0
    kd: float = 2.0
    ki: float = 8.0
    physics_dt: float = .002
    control_dt: float = .01
    anti_windup: bool = True
    disturbance: bool = False
    delay_samples: int = 0
    noise_q: float = 0.0
    noise_v: float = 0.0
    seed: int = 7


def reference_at(case, t):
    if case.reference == 'smooth':
        return quintic(t, case.move_time, case.goal)
    if case.reference == 'step':
        return case.goal, 0.0, 0.0
    if case.reference == 'windup_demo':
        return (1.2 if t < 3.0 else .2), 0.0, 0.0
    raise ValueError('unknown reference')


def preflight(case):
    if case.controller not in ('p', 'pd', 'pid', 'pd_g', 'ff_pd'):
        raise ValueError('unknown controller')
    if case.reference not in ('smooth', 'step', 'windup_demo'):
        raise ValueError('unknown reference')
    vals = [case.goal, case.move_time, case.end_time, case.kp, case.kd, case.ki,
            case.physics_dt, case.control_dt, case.noise_q, case.noise_v]
    if not all(math.isfinite(v) for v in vals):
        raise ValueError('non-finite configuration')
    if min(case.move_time, case.end_time, case.physics_dt, case.control_dt) <= 0:
        raise ValueError('times must be positive')
    if min(case.kp, case.kd, case.ki, case.noise_q, case.noise_v, case.delay_samples) < 0:
        raise ValueError('gains, noise and delay must be nonnegative')
    if not isinstance(case.delay_samples, int):
        raise ValueError('delay_samples must be an integer')
    if case.end_time < max(1.0, case.move_time):
        raise ValueError('duration must include the motion and at least one second')
    ratio = case.control_dt / case.physics_dt
    if not math.isclose(ratio, round(ratio)) or ratio < 1:
        raise ValueError('control period must be an integer multiple of physics step')
    if not math.isclose(case.end_time / case.physics_dt, round(case.end_time / case.physics_dt)):
        raise ValueError('duration must be an integer number of physics steps')
    # 仅 windup_demo 是特意允许不可保持目标的比较案例，普通轨迹仍检查。
    if case.reference == 'windup_demo':
        return None
    if abs(case.goal) > 1.3:
        return 'rejected_joint_target'
    if abs(GRAVITY * math.sin(case.goal)) > LIMIT:
        return 'rejected_static_torque'
    if case.reference == 'smooth':
        vmax, amax = peaks(case.move_time, case.goal)
        if vmax > .6 or amax > 1.0:
            return 'rejected_reference_rate'
    return None


class Controller:
    def __init__(self, case):
        self.case = case
        self.integral = 0.0  # rad*s，当前误差影响下一次积分项。

    def command(self, reference, q, velocity):
        c = self.case
        desired, desired_v, desired_a = reference
        error = desired - q
        base = c.kp * error
        if c.controller != 'p':
            base += c.kd * (desired_v - velocity)
        if c.controller == 'pd_g':
            base += GRAVITY * math.sin(q)
        elif c.controller == 'ff_pd':
            base += INERTIA * desired_a + DAMPING * desired_v + GRAVITY * math.sin(desired)
        raw = base + (c.ki * self.integral if c.controller == 'pid' else 0.0)
        applied = clip(raw)
        # 条件积分：饱和时若误差继续推动同向饱和，冻结积分；反向误差允许释放。
        if c.controller == 'pid':
            pushes_out = (raw >= LIMIT and error > 0) or (raw <= -LIMIT and error < 0)
            if not c.anti_windup or not pushes_out:
                self.integral += error * c.control_dt
        return raw, applied


def run_case(case):
    rejected = preflight(case)
    if rejected:
        return {'config': asdict(case), 'status': rejected, 'steps': 0}, []
    import mujoco
    model = mujoco.MjModel.from_xml_path(str(MODEL))
    model.opt.timestep = case.physics_dt
    model.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
    data = mujoco.MjData(model)  # q=v=0；只初始化，循环不写 qpos/qvel。
    controller = Controller(case)
    every = round(case.control_dt / case.physics_dt)
    rng = random.Random(case.seed)
    history = [(0.0, 0.0)] * (case.delay_samples + 1)
    rows, raw, applied = [], 0.0, 0.0
    nctrl = nsaturated = 0
    status = 'completed'
    for step in range(round(case.end_time / case.physics_dt)):
        t = float(data.time)
        if step % every == 0:
            history.append((float(data.qpos[0]), float(data.qvel[0])))
            history = history[-(case.delay_samples + 1):]
            measured_q, measured_v = history[0]
            measured_q += rng.gauss(0, case.noise_q)
            measured_v += rng.gauss(0, case.noise_v)
            raw, applied = controller.command(reference_at(case, t), measured_q, measured_v)
            nctrl += 1
            nsaturated += abs(raw - applied) > 1e-12
        data.ctrl[0] = applied
        data.qfrc_applied[0] = -.5 if case.disturbance and 3.0 <= t < 4.0 else 0.0
        mujoco.mj_step(model, data)
        # 统一在步后当前状态记录 q、v、实际执行器力矩与参考。
        mujoco.mj_forward(model, data)
        q, v, t = float(data.qpos[0]), float(data.qvel[0]), float(data.time)
        ref, ref_v, ref_a = reference_at(case, t)
        actual = float(data.qfrc_actuator[0])
        rows.append({'t': t, 'q': q, 'v': v, 'ref': ref, 'error': ref-q, 'raw': raw,
                     'tau': actual, 'integral': controller.integral, 'external': float(data.qfrc_applied[0])})
        if not all(math.isfinite(x) for x in (q, v, raw, actual)) or abs(q) > 2.5 or abs(v) > 20:
            data.ctrl[0] = 0
            status = 'aborted_state_bound'
            break  # 只终止本仿真，不表示给真机下发零力矩就是安全停止。
    tail = [r for r in rows if r['t'] >= case.end_time - 1.0 - 1e-9]
    rms = lambda seq: math.sqrt(sum(r['error']**2 for r in seq) / len(seq)) if seq else None
    metrics = {'config': asdict(case), 'status': status, 'steps': len(rows),
               'rmse_rad': rms(rows), 'last_second_rmse_rad': rms(tail),
               'final_speed_rad_s': rows[-1]['v'],
               'final_error_rad': rows[-1]['error'], 'max_abs_error_rad': max(abs(r['error']) for r in rows),
               'max_abs_tau_nm': max(abs(r['tau']) for r in rows),
               'max_abs_raw_nm': max(abs(r['raw']) for r in rows),
               'saturation_control_fraction': nsaturated/nctrl,
               'max_abs_integral_rad_s': max(abs(r['integral']) for r in rows),
               'max_overshoot_rad': max(0.0, max(r['q']-r['ref'] for r in rows)),
               'end_time_s': rows[-1]['t']}
    # 只定义本案例的尾段判据，不将轨迹全程 RMSE 与到位混为一谈。
    metrics['terminal_criterion_met'] = (status == 'completed' and
        abs(rows[-1]['error']) <= .01 and abs(rows[-1]['v']) <= .02 and rms(tail) <= .01)
    return metrics, rows


def cases():
    return ([Case('step_' + mode, controller=mode, reference='step') for mode in ('p', 'pd', 'pid', 'pd_g')]
            + [Case('smooth_pd', controller='pd'), Case('smooth_ff_pd'),
               Case('disturbed_ff_pd', disturbance=True),
               Case('delayed_ff_pd', delay_samples=10),
               Case('noisy_ff_pd', noise_q=.001, noise_v=.01),
               Case('windup_naive', controller='pid', reference='windup_demo', anti_windup=False),
               Case('windup_conditional', controller='pid', reference='windup_demo'),
               Case('reject_horizontal', goal=math.pi/2), Case('reject_torque', goal=1.2),
               Case('reject_fast', move_time=.5)])


def figures(traces, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True, layout='constrained')
    for name, label in [('step_p','P'), ('step_pd','PD'), ('step_pid','PID'), ('step_pd_g','PD + gravity')]:
        rows=traces[name]
        axes[0].plot([r['t'] for r in rows], [r['q'] for r in rows], label=label)
    axes[0].axhline(.5, color='black', linestyle='--', linewidth=1, label='Target 0.5 rad')
    axes[0].set(ylabel='Joint angle (rad)', title='Same rod, same step target, different feedback laws')
    axes[0].legend(ncol=3)
    for name, label in [('smooth_pd','PD'), ('smooth_ff_pd','Feedforward + PD'), ('disturbed_ff_pd','FF + PD, disturbance')]:
        rows=traces[name]
        axes[1].plot([r['t'] for r in rows],[r['error'] for r in rows],label=label)
    axes[1].axvspan(3,4,color='gray',alpha=.12)
    axes[1].set(xlabel='Simulation time (s)',ylabel='Tracking error (rad)',title='Smooth reference; extra -0.5 N m disturbance from 3 to 4 s')
    axes[1].legend()
    for ax in axes: ax.grid(alpha=.2)
    fig.savefig(destination/'tracking.svg')
    fig2, axes2 = plt.subplots(2,1,figsize=(8,5.5),sharex=True,layout='constrained')
    for name,label in [('windup_naive','Integral always updates'),('windup_conditional','Conditional integration')]:
        rows=traces[name]; ts=[r['t'] for r in rows]
        axes2[0].plot(ts,[r['q'] for r in rows],label=label)
        axes2[1].plot(ts,[r['integral'] for r in rows],label=label)
    rows=traces['windup_naive']
    axes2[0].plot([r['t'] for r in rows],[r['ref'] for r in rows],'k--',label='Reference')
    axes2[0].set(ylabel='Joint angle (rad)',title='Deliberately infeasible target, then return to 0.2 rad')
    axes2[1].set(xlabel='Simulation time (s)',ylabel='Integral of error (rad s)')
    for ax in axes2: ax.grid(alpha=.2); ax.legend()
    fig2.savefig(destination/'windup.svg')
    return fig,fig2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plot',action='store_true',help='生成正文 SVG；需要 Matplotlib')
    parser.add_argument('--output',type=Path,default=HERE/'results')
    args=parser.parse_args()
    import mujoco
    results,traces={},{}
    for case in cases():
        metrics,rows=run_case(case)
        results[case.name]=metrics;traces[case.name]=rows
        print(case.name,metrics['status'], 'tail_rmse=',metrics.get('last_second_rmse_rad'),
              'sat=',metrics.get('saturation_control_fraction'), 'integral=',metrics.get('max_abs_integral_rad_s'))
    args.output.mkdir(parents=True,exist_ok=True)
    report={'environment':{'python':platform.python_version(),'mujoco':mujoco.__version__},
            'model':str(MODEL.relative_to(HERE.parent.parent.parent)),
            'criteria':{'final_error_rad':.01,'final_speed_rad_s':.02,'last_second_rmse_rad':.01},
            'cases':results}
    (args.output/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if args.plot: figures(traces,args.output)


if __name__=='__main__':
    main()
