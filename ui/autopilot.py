"""AutoPilot Autonomous Agent Workflow UI for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState
from agent.planner import AgentPlanner
from agent.executor import AgentExecutor
from agent.models import ActionStatus, ActionRisk

def render_autopilot(state: SessionState):
    """Render the autonomous agent workflow, plan view, and live decision trace."""
    st.markdown("## 🤖 AutoPilot Agent Workflow")
    st.markdown("Autonomous Perceive &rarr; Plan &rarr; Act &rarr; Validate &rarr; Adapt &rarr; Report cycle.")

    if state.current_df is None:
        st.info("No active dataset. Please upload or load a sample dataset in the Overview tab.")
        return

    profile = state.current_profile
    issues = profile.get("issues", [])

    # Agent Control Bar
    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 2])
    
    with col_btn1:
        if st.button("🧠 Formulate Plan", use_container_width=True, type="primary"):
            state.plan = AgentPlanner.create_cleaning_plan(profile)
            state.logger.log(
                event_type="PLAN_CREATED",
                decision_summary=f"Formulated structured action plan containing {len(state.plan)} prioritized action(s).",
                details={"plan_length": len(state.plan)}
            )
            st.success(f"Formulated plan with {len(state.plan)} action(s)!")
            st.rerun()

    with col_btn2:
        if state.plan:
            safe_actions = [a for a in state.plan if a.risk_level == ActionRisk.SAFE and a.status == ActionStatus.PENDING]
            if st.button(f"⚡ Execute Safe ({len(safe_actions)})", use_container_width=True):
                with st.spinner("Executing safe operations..."):
                    for act in safe_actions:
                        state.push_snapshot(f"AutoPilot before {act.action_id}")
                        new_df, act, ev = AgentExecutor.execute_action(state.current_df, act, state.session_id)
                        state.update_after_mutation(new_df, f"Executed {act.action_id}")
                    st.rerun()

    with col_btn3:
        if state.plan:
            pending_actions = [a for a in state.plan if a.status == ActionStatus.PENDING]
            if st.button(f"🚀 Execute Approved Actions ({len(pending_actions)})", use_container_width=True):
                with st.spinner("Executing planned actions with validation..."):
                    for act in pending_actions:
                        state.push_snapshot(f"AutoPilot before {act.action_id}")
                        new_df, act, ev = AgentExecutor.execute_action(state.current_df, act, state.session_id)
                        state.update_after_mutation(new_df, f"Executed {act.action_id}")
                    st.rerun()

    st.markdown("---")

    # If no plan generated yet, prompt user
    if not state.plan:
        st.info(f"Perceived **{len(issues)} data quality issue(s)** in current dataset. Click **'🧠 Formulate Plan'** above to let the agent construct an ordered cleaning strategy.")
        
        # Show perceived issues
        if issues:
            st.markdown("### 📋 Perceived Findings (Stage 1: Perception)")
            for iss in issues:
                st.markdown(
                    f"<div class='event-entry'>"
                    f"<strong>[{iss['severity']}] {iss['type']}</strong>: {iss['description']} "
                    f"<span style='color: #22D3EE;'>&rarr; Recommended: {iss.get('suggested_action', 'review')}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        return

    # Two column layout: Active Plan & Live Trace
    plan_col, trace_col = st.columns([3, 2])

    with plan_col:
        st.markdown(f"### 📋 Action Plan ({len(state.plan)} Planned Operations)")
        st.caption("Ordered by priority and dependency. High-risk actions require explicit approval.")

        for idx, action in enumerate(state.plan):
            # Badge for risk
            risk_badge = (
                f"<span class='badge-safe'>SAFE</span>" if action.risk_level == ActionRisk.SAFE
                else f"<span class='badge-review'>REVIEW</span>" if action.risk_level == ActionRisk.REVIEW_RECOMMENDED
                else f"<span class='badge-high-risk'>HIGH RISK</span>"
            )

            # Badge for status
            status_color = (
                "#10B981" if action.status == ActionStatus.PASSED
                else "#EF4444" if action.status in [ActionStatus.FAILED, ActionStatus.ROLLED_BACK]
                else "#38BDF8" if action.status == ActionStatus.EXECUTING
                else "#94A3B8"
            )
            status_badge = f"<span style='color: {status_color}; font-weight: bold;'>{action.status}</span>"

            with st.container():
                st.markdown(
                    f"<div class='datapilot-card'>"
                    f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
                    f"<div><strong>{action.action_id}</strong> &bull; {risk_badge}</div>"
                    f"<div>{status_badge}</div>"
                    f"</div>"
                    f"<div style='margin-top: 8px; color: #F8FAFC;'><strong>Operation:</strong> <code>{action.operation_name}</code> on <code>{', '.join(action.target_columns)}</code></div>"
                    f"<div style='margin-top: 4px; color: #94A3B8; font-size: 13px;'>{action.reason}</div>",
                    unsafe_allow_html=True
                )

                # Action Execution Button if pending
                if action.status == ActionStatus.PENDING:
                    col_run, col_skip = st.columns([1, 1])
                    with col_run:
                        if st.button(f"▶️ Run {action.action_id}", key=f"run_{action.action_id}", use_container_width=True):
                            state.push_snapshot(f"Manual step before {action.action_id}")
                            with st.spinner(f"Executing {action.action_id}..."):
                                new_df, act, ev = AgentExecutor.execute_action(state.current_df, action, state.session_id)
                                state.update_after_mutation(new_df, f"Executed {action.action_id}")
                                st.rerun()
                    with col_skip:
                        if st.button(f"⏭️ Skip", key=f"skip_{action.action_id}", use_container_width=True):
                            action.status = ActionStatus.SKIPPED
                            state.logger.log(
                                event_type="ACTION_SKIPPED",
                                decision_summary=f"User skipped action {action.action_id}.",
                                action_id=action.action_id,
                                status="SKIPPED"
                            )
                            st.rerun()

                # If executed, show validation result
                elif action.validation_result:
                    v_res = action.validation_result
                    v_color = "#10B981" if v_res.get("is_valid") else "#EF4444"
                    st.markdown(
                        f"<div style='margin-top: 6px; padding: 6px; background: rgba(0,0,0,0.3); border-radius: 4px; font-size: 12px; color: {v_color};'>"
                        f"<strong>Validation:</strong> {v_res.get('reason')}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                st.markdown("</div>", unsafe_allow_html=True)

    with trace_col:
        st.markdown("### 📡 Live Agent Decision Trace")
        st.caption("Verifiable audit timeline of agent perception, actions, and validation results.")
        
        events = state.logger.get_events()
        if not events:
            st.info("No events logged yet.")
        else:
            # Show in reverse chronological order
            for ev in reversed(events[-15:]):
                ev_color = (
                    "#10B981" if "PASSED" in ev.status or "COMPLETED" in ev.status
                    else "#EF4444" if "ROLLBACK" in ev.event_type or "FAILED" in ev.status
                    else "#38BDF8"
                )
                st.markdown(
                    f"<div class='event-entry' style='border-left-color: {ev_color};'>"
                    f"<span class='event-time'>{ev.timestamp}</span> "
                    f"<strong style='color: {ev_color};'>{ev.event_type}</strong><br>"
                    f"<span style='color: #F8FAFC;'>{ev.decision_summary}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
