"""第七章解析合成数据辨识；不运行 MuJoCo，不连接硬件。"""

import argparse
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
BASE = (.24, .2, 5.886)  # I: kg*m²，b: N*m*s/rad，k: N*m
TRUTH = (.42, .2, 8.829)  # 原单杆末端刚性固定 0.5 kg 质点


def motion(t, validation=False):
    """解析 q、v、a，单位 rad、rad/s、rad/s²；不把参考当成机器人实测。"""
    import numpy as np
    offset, a1, w1, p1, a2, w2, p2 = (
        (.1, .3, .8, .4, .1, 2.2, 0.) if validation
        else (0., .35, 1.1, 0., .12, 2.7, .3))
    q = offset + a1*np.sin(w1*t+p1) + a2*np.sin(w2*t+p2)
    v = a1*w1*np.cos(w1*t+p1) + a2*w2*np.cos(w2*t+p2)
    a = -a1*w1*w1*np.sin(w1*t+p1) - a2*w2*w2*np.sin(w2*t+p2)
    return q, v, a


def regressor(q, v, a):
    import numpy as np
    return np.column_stack((a, v, np.sin(q)))


def fit(x, torque, max_condition=1e4):
    """按列 RMS 缩放后用 SVD 最小二乘；秩不足等情况不给出可用参数。"""
    import numpy as np
    x, torque = np.asarray(x, float), np.asarray(torque, float)
    if x.ndim != 2 or x.shape[1] != 3 or len(x) < 3 or torque.shape != (len(x),):
        raise ValueError('expected X with shape (N, 3), torque with shape (N,), N >= 3')
    if not (np.isfinite(x).all() and np.isfinite(torque).all()):
        raise ValueError('non-finite data')
    scales = np.sqrt(np.mean(x*x, axis=0))
    scales[scales == 0] = 1.0
    scaled = x / scales
    beta, _, rank, singular = np.linalg.lstsq(scaled, torque, rcond=None)
    report = {'rank': int(rank), 'column_rms': scales.tolist(),
              'scaled_singular_values': singular.tolist(), 'theta': None}
    if rank < 3:
        return dict(report, status='rejected_rank', scaled_condition=None)
    condition = float(singular[0]/singular[-1])
    report['scaled_condition'] = condition
    if condition > max_condition:
        return dict(report, status='rejected_condition')
    theta = beta/scales
    if not (theta[0] > 0 and theta[1] >= 0 and theta[2] > 0):
        return dict(report, status='rejected_physical_sign')
    return dict(report, status='fitted', theta=theta.tolist())


def rms(values):
    import numpy as np
    return float(np.sqrt(np.mean(np.asarray(values)**2)))


def identification():
    import numpy as np
    train_t = np.linspace(0, 10, 1001)
    validation_t = np.linspace(0, 6, 601)
    q, v, a = motion(train_t)
    qt, vt, at = motion(validation_t, validation=True)
    x, xt = regressor(q,v,a), regressor(qt,vt,at)
    clean, clean_test = x@TRUTH, xt@TRUTH
    noise = np.random.default_rng(7).normal(0, .03, len(train_t))
    results, traces = {}, {'t': validation_t, 'true': clean_test}
    for name, train_tau, test_tau in (
        ('noiseless', clean, clean_test),
        ('torque_noise', clean+noise, clean_test),
        ('missing_friction', clean+.12*np.tanh(v/.02)+noise,
         clean_test+.12*np.tanh(vt/.02))):
        result = fit(x, train_tau)
        if result['status'] == 'fitted':
            theta = result['theta']
            result.update(train_torque_rmse_nm=rms(x@theta-train_tau),
                          validation_torque_rmse_nm=rms(xt@theta-test_tau),
                          base_validation_torque_rmse_nm=rms(xt@BASE-test_tau),
                          validation_max_abs_error_nm=float(np.max(np.abs(xt@theta-test_tau))))
            traces[name] = xt@theta-test_tau
        results[name] = result
    angles = np.linspace(-.5,.5,21)
    static = regressor(angles, np.zeros(21), np.zeros(21))
    results['static_only'] = fit(static, static@TRUTH)
    # 很小振幅的单频运动，a≈-w² sin(q)，两列几乎相关。
    w = 1.1
    small_q = .01*np.sin(w*train_t)
    weak = regressor(small_q, .01*w*np.cos(w*train_t), -w*w*small_q)
    results['weak_excitation'] = fit(weak, weak@TRUTH)
    wrong_sign = x@np.array([-.42, .2, 8.829])
    results['negative_inertia'] = fit(x, wrong_sign)
    report = {'data_source': 'analytic synthetic data; no physics simulation or hardware',
              'environment': {'python': platform.python_version(), 'numpy': np.__version__},
              'parameter_order': ['I_kg_m2','b_nm_s_per_rad','k_nm'],
              'truth': list(TRUTH), 'unloaded_base': list(BASE),
              'settings': {'train_samples': 1001, 'validation_samples': 601,
                           'sample_period_s': .01, 'torque_noise_sigma_nm': .03,
                           'seed': 7, 'max_scaled_condition': 1e4,
                           'missing_friction': '.12*tanh(v/.02) N*m'},
              'cases': results}
    return report, traces


def plot(traces, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8,4), layout='constrained')
    for name, label in [('noiseless','Exact model, exact data'),
                        ('torque_noise','Exact model, noisy training torque'),
                        ('missing_friction','Friction omitted from fitted model')]:
        ax.plot(traces['t'],traces[name], label=label)
    ax.axhline(0, color='black', linewidth=.6)
    ax.set(xlabel='Held-out trajectory time (s)', ylabel='Predicted minus true torque (N m)',
           title='Synthetic identification: validation on a different motion')
    ax.grid(alpha=.2)
    ax.legend()
    fig.savefig(output/'validation.svg')
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--output',type=Path,default=HERE/'results')
    args = parser.parse_args()
    report, traces = identification()
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    for name, result in report['cases'].items():
        print(name, result)
    if args.plot:
        plot(traces,args.output)


if __name__ == '__main__':
    main()
