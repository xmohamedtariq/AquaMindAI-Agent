from src.agent.planner import AgentAction, Planner
from src.agent.state import AgentState, TerminationReason


def make_state() -> AgentState:
    return AgentState(
        task_id="test-task-001",
        user_request="Investigate desalination plant performance",
    )


def add_completed_step(
    state: AgentState,
    action: AgentAction,
) -> None:
    state.add_observation(
        source=action.value,
        content={"success": True},
    )


def test_initial_plan_contains_complete_workflow():
    state = make_state()
    planner = Planner()

    plan = planner.build_initial_plan(state)

    assert plan == [
        "validate_sensor_data",
        "calculate_plant_kpis",
        "detect_anomalies",
        "search_operational_knowledge",
        "search_incident_memory",
        "diagnose_issue",
        "generate_incident_report",
        "final_answer",
    ]

    assert state.plan == plan


def test_full_planning_sequence():
    state = make_state()
    planner = Planner()

    # 1 — validation
    decision = planner.next_action(state)
    assert decision.action == AgentAction.VALIDATE_DATA

    add_completed_step(
        state,
        AgentAction.VALIDATE_DATA,
    )

    # 2 — KPIs
    decision = planner.next_action(state)
    assert decision.action == AgentAction.CALCULATE_KPIS

    add_completed_step(
        state,
        AgentAction.CALCULATE_KPIS,
    )

    # 3 — anomalies
    decision = planner.next_action(state)
    assert decision.action == AgentAction.DETECT_ANOMALIES

    add_completed_step(
        state,
        AgentAction.DETECT_ANOMALIES,
    )

    # 4 — operational knowledge
    decision = planner.next_action(state)
    assert decision.action == AgentAction.SEARCH_KNOWLEDGE

    add_completed_step(
        state,
        AgentAction.SEARCH_KNOWLEDGE,
    )

    # 5 — incident memory
    decision = planner.next_action(state)
    assert decision.action == AgentAction.SEARCH_MEMORY

    add_completed_step(
        state,
        AgentAction.SEARCH_MEMORY,
    )

    # 6 — diagnosis
    decision = planner.next_action(state)
    assert decision.action == AgentAction.DIAGNOSE

    add_completed_step(
        state,
        AgentAction.DIAGNOSE,
    )

    # 7 — report
    decision = planner.next_action(state)
    assert decision.action == AgentAction.GENERATE_REPORT

    add_completed_step(
        state,
        AgentAction.GENERATE_REPORT,
    )

    # 8 — final answer
    decision = planner.next_action(state)

    assert decision.action == AgentAction.FINALIZE

    assert (
        decision.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_budget_limit_stops_agent():
    state = make_state()
    state.cumulative_cost_usd = 0.10

    planner = Planner()
    decision = planner.next_action(state)

    assert decision.action == AgentAction.STOP

    assert (
        decision.termination_reason
        == TerminationReason.BUDGET_LIMIT_REACHED
    )


def test_max_turns_stops_agent():
    state = make_state()
    state.turn_count = 12

    planner = Planner()
    decision = planner.next_action(state)

    assert decision.action == AgentAction.STOP

    assert (
        decision.termination_reason
        == TerminationReason.MAX_TURNS_REACHED
    )


def test_max_tool_calls_stops_agent():
    state = make_state()
    state.tool_call_count = 20

    planner = Planner()
    decision = planner.next_action(state)

    assert decision.action == AgentAction.STOP

    assert (
        decision.termination_reason
        == TerminationReason.MAX_TOOL_CALLS_REACHED
    )