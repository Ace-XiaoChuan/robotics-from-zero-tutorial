"""核对 18～20 的人工代数和接口示例；不训练或执行机器人策略。"""

import json
import math
import platform


def close(actual, expected, tolerance=1e-9):
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{actual} != {expected}")


def vector_close(actual, expected):
    assert len(actual) == len(expected)
    for first, second in zip(actual, expected):
        close(first, second)


def difference(function, value, step=1e-6):
    return (function(value + step) - function(value - step)) / (2 * step)


def discounted_return(rewards, gamma):
    # 从后往前递推，与正文的幂展开独立比较。
    value = 0.0
    for reward in reversed(rewards):
        value = reward + gamma * value
    return value


def action_chunk(episode, start, horizon):
    """只从当前 episode 取标签；填充位置不计入损失。"""
    valid = episode[start:start + horizon]
    return valid + [0.0] * (horizon - len(valid)), [True] * len(valid) + [False] * (horizon - len(valid))


def wilson(successes, attempts, z=1.96):
    if attempts <= 0 or not 0 <= successes <= attempts:
        raise ValueError("无效任务计数")
    proportion = successes / attempts
    denominator = 1 + z * z / attempts
    center = (proportion + z * z / (2 * attempts)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / attempts + z * z / (4 * attempts**2)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def hold_time(times, errors, tolerance=0.01, duration=0.5):
    if len(times) != len(errors) or any(second <= first for first, second in zip(times, times[1:])):
        raise ValueError("时间与误差需对齐且严格递增")
    entered = None
    for timestamp, error in zip(times, errors):
        if not math.isfinite(error) or abs(error) > tolerance:
            entered = None
        elif entered is None:
            entered = timestamp
        if entered is not None and timestamp - entered >= duration - 1e-12:
            return timestamp
    return None


def constrained_increment(position, requested, age, limit=0.01, bounds=(0.0, 0.30), max_age=0.2):
    """一维教学筛选；不检查 IK、碰撞、制动或执行器动力学。"""
    if any(not math.isfinite(value) for value in (position, requested, age)):
        raise ValueError("输入必须有限")
    if not bounds[0] <= position <= bounds[1] or not 0 <= age <= max_age:
        raise ValueError("位置或观测时效无效")
    limited = max(-limit, min(limit, requested))
    target = max(bounds[0], min(bounds[1], position + limited))
    return target - position


def main():
    results = {}

    features, labels = [0.1, 0.2, -0.1], [0.02, 0.04, -0.02]
    loss = lambda gain: sum((gain * error - label)**2 for error, label in zip(features, labels)) / len(labels)
    fitted = sum(error * label for error, label in zip(features, labels)) / sum(error**2 for error in features)
    close(fitted, 0.2)
    close(loss(0.1), 0.0002)
    close(difference(loss, 0.1), -0.004)
    close(difference(loss, fitted), 0)
    assert all(loss(fitted + offset) > loss(fitted) for offset in (-0.1, -0.01, 0.01, 0.1))
    results["18_bc_fit"] = {"k": fitted, "initial_mse_m2": loss(0.1), "initial_rmse_m": math.sqrt(loss(0.1)), "gradient": difference(loss, 0.1)}

    current, value, dt = 0.2, 0.02, 0.1
    endpoints = {"increment_m": current + value, "absolute_target_m": value, "velocity_m_per_s": current + value * dt}
    vector_close(list(endpoints.values()), [0.22, 0.02, 0.202])
    results["18_action_semantics"] = endpoints

    position, goal = 0.2, 0.3
    reaching = [position]
    for _ in range(20):
        position += 0.2 * (goal - position)
        reaching.append(position)
    vector_close(reaching[1:4], [0.22, 0.236, 0.2488])
    for step, position in enumerate(reaching):
        close(goal - position, 0.1 * 0.8**step)
    results["18_reaching_feedback"] = {"positions_first_three_m": reaching[1:4], "error_step20_m": goal - reaching[-1]}

    replay_error, feedback_error = [0.0], [0.0]
    bias, gain = 0.001, 0.2
    for step in range(1, 21):
        replay_error.append(replay_error[-1] + bias)
        feedback_error.append((1 - gain) * feedback_error[-1] + bias)
        close(replay_error[-1], step * bias)
        close(feedback_error[-1], bias * sum((1 - gain)**i for i in range(step)))
        assert 0 <= feedback_error[-1] < bias / gain
    results["18_bias_accumulation"] = {"dt_s": dt, "replay_error_m": replay_error, "feedback_error_m": feedback_error, "limit_m": bias / gain}

    expert_action = 0.2 * (0.3 - 0.32)
    close(expert_action, -0.004)
    assert abs(0.3 - (0.32 + expert_action)) < abs(0.3 - 0.32)
    assert abs(0.3 - (0.32 + 0.004)) > abs(0.3 - 0.32)
    results["18_dagger_recovery_label"] = {"visited_position_m": 0.32, "expert_increment_m": expert_action}

    chunk = [0.2 * 0.1 * 0.8**index for index in range(4)]
    vector_close(chunk, [0.02, 0.016, 0.0128, 0.01024])
    close(0.2 + sum(chunk[:2]), 0.236)
    close(chunk[2], 0.2 * (goal - 0.236))
    padded, mask = action_chunk(chunk, 2, 4)
    assert mask == [True, True, False, False]
    valid_loss = sum((pred - truth)**2 for pred, truth, valid in zip([0.0, 0.0, 99.0, 99.0], padded, mask) if valid) / sum(mask)
    close(valid_loss, (chunk[2]**2 + chunk[3]**2) / 2)
    results["18_action_chunk_alignment"] = {"chunk_m": chunk, "executed_prefix_steps": 2, "replan_position_m": 0.236, "tail_valid_mask": mask}

    target_predictions, weights = [0.250, 0.254], [2, 1]
    ensemble = sum(weight * action for weight, action in zip(weights, target_predictions)) / sum(weights)
    close(ensemble, 0.2513333333333333)
    assert min(target_predictions) < ensemble < max(target_predictions)
    close(sum(10 * weight * action for weight, action in zip(weights, target_predictions)) / sum(10 * weight for weight in weights), ensemble)
    results["18_same_time_ensemble"] = {"same_execution_time_targets_m": target_predictions, "weights": weights, "combined_target_m": ensemble}

    close(discounted_return([-1, -1, 10], 0.9), 6.2)
    close(discounted_return([-0.1, 1], 0.9), 0.8)
    close(discounted_return([-0.1, -0.1, 1], 0.9), 0.62)
    results["19_returns"] = {"three_reward_return": 6.2, "advance_return": 0.8, "wait_then_advance_return": 0.62}

    gamma_new = math.sqrt(0.9)
    close(gamma_new**20, 0.9**10)
    results["19_discount_time_scale"] = {"weight_after_10_steps": 0.9**10, "gamma_at_half_dt": gamma_new}

    transitions = {"S0": [("S1", -0.1), ("S0", -0.1)], "S1": [("G", 1.0), ("S1", -0.1)], "G": []}
    values = {state: 0.0 for state in transitions}
    for _ in range(20):
        values = {state: max((reward + 0.9 * values[next_state] for next_state, reward in actions), default=0.0) for state, actions in transitions.items()}
    vector_close([values["S0"], values["S1"], values["G"]], [0.8, 1, 0])
    action_values = {state: [reward + 0.9 * values[next_state] for next_state, reward in actions] for state, actions in transitions.items()}
    vector_close(action_values["S0"], [0.8, 0.62])
    vector_close(action_values["S1"], [1, 0.8])
    results["19_bellman_values"] = {"V": values, "Q_advance_wait": action_values}

    q = {"S0": 0.0, "S1": 0.0}
    q_updates = []
    for state in ["S1", "S0", "S1", "S0"]:
        target = 1.0 if state == "S1" else -0.1 + 0.9 * max(q["S1"], 0)
        q[state] += 0.5 * (target - q[state])
        q_updates.append(q[state])
    vector_close(q_updates, [0.5, 0.175, 0.75, 0.375])
    results["19_q_learning_updates"] = {"updates": q_updates}

    sigmoid = lambda theta: 1 / (1 + math.exp(-theta))
    p = sigmoid(0)
    score_gradients, rewards = [1 - p, -p], [1, 0]
    expected_gradient = sum(prob * score * reward for prob, score, reward in zip([p, 1 - p], score_gradients, rewards))
    baseline_gradient = sum(prob * score * (reward - 0.5) for prob, score, reward in zip([p, 1 - p], score_gradients, rewards))
    close(expected_gradient, 0.25)
    close(baseline_gradient, expected_gradient)
    close(difference(sigmoid, 0), expected_gradient)
    close(sum(prob * score for prob, score in zip([p, 1 - p], score_gradients)), 0)
    results["19_policy_gradient"] = {"probability": p, "expected_gradient": expected_gradient, "baseline_gradient": baseline_gradient, "sample_gradients_with_baseline": [score * (reward - 0.5) for score, reward in zip(score_gradients, rewards)]}

    clipped_objective = lambda ratio, advantage: min(ratio * advantage, max(0.8, min(1.2, ratio)) * advantage)
    close(clipped_objective(1.3, 2), 2.4)
    close(clipped_objective(0.7, -2), -1.6)
    close(difference(lambda ratio: clipped_objective(ratio, 2), 1.3), 0)
    close(difference(lambda ratio: clipped_objective(ratio, -2), 0.7), 0)
    close(difference(lambda ratio: clipped_objective(ratio, 2), 0.9), 2)
    close(difference(lambda ratio: clipped_objective(ratio, -2), 1.1), -2)
    results["19_ppo_clip"] = {"positive_advantage": 2.4, "negative_advantage": -1.6, "outside_improvement_gradients": [0, 0]}

    target_sac = lambda terminal: -0.1 + 0.9 * (1 - terminal) * (min(0.8, 1.0) - 0.1 * (-0.5))
    close(target_sac(False), 0.665)
    close(target_sac(True), -0.1)
    results["19_sac_critic_target"] = {"nonterminal_target": target_sac(False), "terminal_target": target_sac(True), "without_entropy": -0.1 + 0.9 * 0.8}

    amplitude = 0.05
    squash = lambda u: amplitude * math.tanh(u)
    close(squash(2), 0.04820137900379085)
    close(difference(squash, 2), amplitude * (1 - math.tanh(2)**2))
    close(-math.log(amplitude), 2.995732273553991)
    def density(action):
        u = math.atanh(action / amplitude)
        normal = math.exp(-u * u / 2) / math.sqrt(2 * math.pi)
        return normal / (amplitude * (1 - (action / amplitude)**2))
    # 在物理动作坐标积分，和原高斯 u∈[-3,3] 的 CDF 独立比较。
    lower, upper, intervals = squash(-3), squash(3), 20000
    width = (upper - lower) / intervals
    integrated_mass = width * sum(density(lower + (i + 0.5) * width) for i in range(intervals))
    close(integrated_mass, math.erf(3 / math.sqrt(2)), tolerance=1e-6)
    assert density(0) > 1
    results["19_squashed_density"] = {"increment_at_u2_m": squash(2), "log_scale_correction_at_u0": -math.log(amplitude), "density_at_zero": density(0), "integrated_probability_u_minus3_to3": integrated_mass}

    def value_target(reward, next_value, terminated):
        return reward + 0.9 * (1 - terminated) * next_value
    close(value_target(-0.1, 0.8, True), -0.1)
    close(value_target(-0.1, 0.8, False), 0.62)
    results["19_terminal_vs_truncation"] = {"terminal_target": -0.1, "external_truncation_target": 0.62, "last_observation_value": 0.8}

    waiting_value = 0.2 / (1 - 0.9)
    close(waiting_value, 2)
    close(discounted_return([0.2] * 300, 0.9), waiting_value)
    assert waiting_value > values["S0"]
    results["19_reward_loophole"] = {"infinite_wait_value": waiting_value, "advance_value": values["S0"]}

    split = {"train": {"A", "B"}, "validation": {"C"}, "test": {"D"}}
    assert not split["train"] & split["validation"] and not split["train"] & split["test"] and not split["validation"] & split["test"]
    assert set.union(*split.values()) == {"A", "B", "C", "D"}
    bad_frame_split = {"train": {"A", "B"}, "test": {"A", "C"}}
    assert bad_frame_split["train"] & bad_frame_split["test"] == {"A"}
    results["20_group_split"] = {key: sorted(value) for key, value in split.items()}

    times = [i / 10 for i in range(7)]
    errors = [0.020, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004]
    close(hold_time(times, errors), 0.6)
    assert hold_time(times[:6], errors[:6]) is None
    assert hold_time(times, [0.020, 0.009, 0.008, 0.011, 0.006, 0.005, 0.004]) is None
    assert hold_time(times, [0.020, 0.009, 0.008, math.nan, 0.006, 0.005, 0.004]) is None
    close(hold_time([i / 10 for i in range(6)], [0.01] * 6), 0.5)
    results["20_success_hold_duration"] = {"success_time_s": 0.6, "five_in_range_samples_duration_s": 0.4, "six_in_range_samples_duration_s": 0.5}

    counts = {"baseline": 18, "new_goal": 15, "new_view": 12, "delay": 11, "combined": 7}
    rates = {name: count / 20 for name, count in counts.items()}
    vector_close(list(rates.values()), [0.9, 0.75, 0.6, 0.55, 0.35])
    assert not math.isclose(rates["new_goal"] * rates["new_view"] * rates["delay"], rates["combined"])
    results["20_artificial_perturbation_counts"] = {"successes": counts, "attempts_each": 20, "rates": rates, "status": "artificial counts, not rollout measurements"}

    interval10, interval100 = wilson(8, 10), wilson(80, 100)
    for successes, attempts, interval in [(8, 10, interval10), (80, 100, interval100)]:
        p_hat = successes / attempts
        for endpoint in interval:
            close(attempts * (endpoint - p_hat)**2 / (endpoint * (1 - endpoint)), 1.96**2)
        inverse = wilson(attempts - successes, attempts)
        close(inverse[0], 1 - interval[1])
        close(inverse[1], 1 - interval[0])
    assert interval10[1] - interval10[0] > interval100[1] - interval100[0]
    close(wilson(0, 10)[0], 0)
    close(wilson(10, 10)[1], 1)
    results["20_wilson_intervals"] = {"8_of_10": interval10, "80_of_100": interval100}

    pooled, balanced = (36 + 2) / (40 + 10), (36 / 40 + 2 / 10) / 2
    close(pooled, 0.76)
    close(balanced, 0.55)
    close((40 / 50) * (36 / 40) + (10 / 50) * (2 / 10), pooled)
    results["20_scene_aggregation"] = {"pooled_rate": pooled, "equal_scene_rate": balanced}

    displacement = lambda mass: 1.0 * 0.2**2 / (2 * mass)
    close(displacement(1), 0.02)
    close(displacement(2), 0.01)
    close(displacement(0.8), 0.025)
    close(displacement(1.2), 1 / 60)
    assert not 0.8 <= 2 <= 1.2
    results["20_mass_mismatch"] = {"force_N": 1, "duration_s": 0.2, "sim_displacement_m": displacement(1), "double_mass_displacement_m": displacement(2), "training_range_displacements_m": [displacement(0.8), displacement(1.2)]}

    latency, velocity, old_position = 0.25, 0.2, 0.2
    now_position = old_position + velocity * latency
    close(now_position, 0.25)
    old_action, now_action = 0.2 * (0.3 - old_position), 0.2 * (0.3 - now_position)
    vector_close([old_action, now_action, old_action - now_action], [0.02, 0.01, 0.01])
    results["20_latency_mismatch"] = {"age_s": latency, "position_offset_m": velocity * latency, "old_increment_m": old_action, "current_increment_m": now_action}

    positive = constrained_increment(0.295, 0.02, 0.1)
    negative = constrained_increment(0.295, -0.02, 0.1)
    vector_close([positive, negative], [0.005, -0.01])
    for position in [0, 0.1, 0.295, 0.3]:
        for request in [-0.1, -0.02, 0, 0.02, 0.1]:
            action = constrained_increment(position, request, 0.2)
            assert abs(action) <= 0.01 + 1e-12 and -1e-12 <= position + action <= 0.3 + 1e-12
    rejected = 0
    for invalid in [(0.295, math.nan, 0.1), (0.295, math.inf, 0.1), (0.295, 0.02, 0.21), (0.295, 0.02, -0.1), (0.31, -0.02, 0.1)]:
        try:
            constrained_increment(*invalid)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("未拒绝无效动作输入")
    assert rejected == 5
    results["20_action_constraints"] = {"positive_executed_m": positive, "negative_executed_m": negative, "invalid_inputs_rejected": rejected, "scope": "1D kinematic bounds only"}

    # 人工记录以初始任务 ID 计数，恢复事件不会创造额外 episode。
    episodes = [{"id": i, "success": i < 16, "recoveries": 1 if 12 <= i < 16 else (2 if i >= 16 else 0)} for i in range(20)]
    assert len({entry["id"] for entry in episodes}) == 20
    assert all(entry["recoveries"] <= 2 for entry in episodes)
    succeeded = sum(entry["success"] for entry in episodes)
    no_recovery = sum(entry["success"] and entry["recoveries"] == 0 for entry in episodes)
    recovered_success = sum(entry["success"] and entry["recoveries"] > 0 for entry in episodes)
    vector_close([succeeded / len(episodes), no_recovery / len(episodes), recovered_success], [0.8, 0.6, 4])
    results["20_recovery_accounting"] = {"successes": succeeded, "initial_tasks": len(episodes), "successes_without_recovery": no_recovery, "successes_with_recovery": recovered_success, "status": "artificial event counts"}

    assert len(results) == 26
    print(json.dumps({"date": "2026-10-12", "python": platform.python_version(), "checks_passed": len(results),
                      "scope": "18-20 artificial labels, analytic feedback, tabular values, probability gradients and evaluation arithmetic; no policy training or robot rollout",
                      "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
