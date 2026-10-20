import numpy as np

from research.run_phase6_policy_baselines import summarize_policy_metrics


def test_policy_baseline_rates_follow_specification():
    decisions = np.array(["APPROVE", "DECLINE", "REVIEW", "REVIEW"])
    policy = np.array(["SATISFIED", "UNSATISFIED", "UNRESOLVED", "SATISFIED"])
    truth = np.array(["SATISFIED", "SATISFIED", "SATISFIED", "UNSATISFIED"])
    pd_values = np.array([0.1, 0.1, 0.2, 0.2])
    outcomes = np.array([0, 0, 0, 1])

    metrics = summarize_policy_metrics(
        decisions, policy, truth, pd_values, tau=0.3, outcomes=outcomes
    )

    assert metrics["violation_rate"] == 0.0
    assert metrics["wrongful_decline_rate"] == 1 / 3
    assert metrics["review_rate"] == 0.5
    assert metrics["referred_truly_eligible_share"] == 0.5
    assert metrics["recovered_count"] == 1.0


def test_wrongful_decline_is_zero_without_true_eligible_low_risk_pool():
    metrics = summarize_policy_metrics(
        decisions=np.array(["DECLINE"]),
        policy_states=np.array(["UNSATISFIED"]),
        true_states=np.array(["UNSATISFIED"]),
        pd_values=np.array([0.1]),
        tau=0.3,
        outcomes=np.array([0]),
    )

    assert metrics["wrongful_decline_rate"] == 0.0
