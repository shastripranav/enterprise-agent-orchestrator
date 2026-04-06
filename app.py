"""Streamlit demo UI for the Enterprise Multi-Agent Orchestrator."""

import streamlit as st

st.set_page_config(
    page_title="Enterprise Agent Orchestrator",
    page_icon="🏢",
    layout="wide",
)


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "provider" not in st.session_state:
        st.session_state.provider = "openai"


def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Configuration")

        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "ollama"],
            index=["openai", "anthropic", "ollama"].index(st.session_state.provider),
        )
        if provider != st.session_state.provider:
            st.session_state.provider = provider
            import os
            os.environ["LLM_PROVIDER"] = provider
            from src.config import reset_config
            from src.orchestrator import reset_orchestrator
            reset_config()
            reset_orchestrator()

        st.divider()
        st.subheader("Sample Queries")
        samples = [
            "What's our Q3 budget utilization?",
            "Show me current SLA compliance",
            "What's on the product roadmap for Q4?",
            "Any critical incidents this week?",
            "What resources do we need for the AI initiative?",
            "Give me an executive summary of Q3",
        ]
        for sample in samples:
            if st.button(sample, key=f"sample_{hash(sample)}", use_container_width=True):
                st.session_state.pending_query = sample
                st.rerun()

        st.divider()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.caption("Built with LangGraph + Streamlit")


def render_routing_info(state: dict):
    meta = state.get("routing_metadata", {})
    if not meta:
        return

    method = meta.get("method", "unknown")
    agent = meta.get("selected_agent", "unknown")
    scores = meta.get("keyword_scores", {})

    agent_colors = {
        "finance": "🟢",
        "operations": "🔵",
        "planning": "🟣",
    }

    with st.expander("🔀 Routing Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Selected Agent", agent.title())
        with col2:
            method_label = {
                "keyword_match": "⚡ Keyword Match (fast path)",
                "llm_fallback": "🤖 LLM Classification",
                "multi_agent_sequential": "🔄 Multi-Agent",
            }.get(method, method)
            st.metric("Routing Method", method_label)

        if scores:
            score_cols = st.columns(3)
            for i, (domain, score) in enumerate(scores.items()):
                with score_cols[i]:
                    emoji = agent_colors.get(domain, "⚪")
                    is_selected = domain == agent
                    st.metric(
                        f"{emoji} {domain.title()}",
                        f"Score: {score}",
                        delta="SELECTED" if is_selected else None,
                    )


def render_agent_responses(state: dict):
    responses = state.get("agent_responses", {})
    if len(responses) <= 1:
        return

    with st.expander("📋 Individual Agent Responses"):
        for domain, content in responses.items():
            st.subheader(f"{domain.title()} Agent")
            st.markdown(content)
            st.divider()


def main():
    init_session()
    render_sidebar()

    st.title("🏢 Enterprise Multi-Agent Orchestrator")
    st.caption(
        "Ask business questions — they're automatically routed to Finance, "
        "Operations, or Planning specialist agents."
    )

    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])
            if role == "assistant" and "state" in msg:
                render_routing_info(msg["state"])
                render_agent_responses(msg["state"])

    # handle pending query from sidebar buttons
    pending = st.session_state.pop("pending_query", None)

    user_input = st.chat_input("Ask about budget, operations, roadmap...")

    query = pending or user_input
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Routing and processing..."):
                from src.orchestrator import run_query
                result = run_query(query)

            final = result.get("final_response", "No response generated.")
            st.markdown(final)
            render_routing_info(result)
            render_agent_responses(result)

        st.session_state.messages.append({
            "role": "assistant",
            "content": final,
            "state": {
                "routing_metadata": result.get("routing_metadata", {}),
                "agent_responses": result.get("agent_responses", {}),
            },
        })


if __name__ == "__main__":
    main()
