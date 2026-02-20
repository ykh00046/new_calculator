"""
AI Section Component - Enhanced AI Analysis interface.

Features:
- Status indicator
- Smart insights cards
- Enhanced chat UI
"""

import streamlit as st
import requests
from typing import Optional


def render_ai_status_indicator(is_online: bool = True) -> None:
    """
    Render AI status indicator.

    Args:
        is_online: Whether the AI service is online
    """
    status_color = "#00aa66" if is_online else "#cc4444"
    status_text = "Online" if is_online else "Offline"
    status_icon = "●" if is_online else "○"

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px;">
        <span style="color: {status_color}; font-size: 1.2rem;">{status_icon}</span>
        <span style="color: {status_color}; font-weight: 600;">AI Status: {status_text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_ai_header_with_animation() -> None:
    """Render AI section header with styling."""
    # Header with gradient text
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 5px;
        ">
            AI Production Analyst
        </h1>
        <p style="color: #888; font-size: 1rem;">
            Ask questions about your production data in natural language
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_smart_insights(insights: list) -> None:
    """
    Render smart insights cards.

    Args:
        insights: List of insight strings to display
    """
    if not insights:
        return

    st.markdown("### Smart Insights")
    cols = st.columns(len(insights))

    for i, insight in enumerate(insights):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            ">
                <p style="margin: 0; color: #333; font-size: 0.9rem;">{insight}</p>
            </div>
            """, unsafe_allow_html=True)


def render_faq_chips() -> Optional[str]:
    """
    Render FAQ chip buttons.

    Returns:
        Selected FAQ query or None
    """
    st.markdown("**Quick Questions:**")
    cols = st.columns(3)
    faq_queries = [
        "Top product last year?",
        "Today's total production?",
        "Average production for BW0021?"
    ]

    selected_faq = None
    for i, q in enumerate(faq_queries):
        if cols[i].button(q, use_container_width=True, key=f"faq_{i}"):
            selected_faq = q

    return selected_faq


def render_ai_chat(api_url: str = "http://localhost:8000/chat/") -> None:
    """
    Render AI chat interface.

    Args:
        api_url: URL of the chat API endpoint
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat container
    chat_container = st.container(height=400)

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input handling
    prompt = st.chat_input("Ask anything about production data...")

    # Check FAQ selection
    selected_faq = render_faq_chips()
    if selected_faq:
        prompt = selected_faq

    if prompt:
        with chat_container:
            st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("Analyzing..."):
                resp = requests.post(api_url, json={"query": prompt}, timeout=60)

            if resp.status_code == 200:
                answer = resp.json().get("answer", "No response")
                with chat_container:
                    st.chat_message("assistant").markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"API Error: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to AI server. Please check if the API is running.")
        except Exception as e:
            st.error(f"Error: {e}")

    # Clear chat button
    if st.button("Clear Chat History", icon="🗑️"):
        st.session_state.messages = []
        st.rerun()


def render_ai_section(api_url: str = "http://localhost:8000/chat/") -> None:
    """
    Render complete AI analysis section.

    Args:
        api_url: URL of the chat API endpoint
    """
    # Apply AI section CSS
    st.markdown("""
    <style>
        /* AI section glow effects */
        [data-testid="stChatMessage"] {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 10px 15px;
            margin: 5px 0;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }

        [data-testid="stChatMessage"][data-testid*="assistant"] {
            border-left: 3px solid #667eea;
        }

        [data-testid="stChatMessage"][data-testid*="user"] {
            border-left: 3px solid #764ba2;
        }

        /* Chat input styling */
        [data-testid="stChatInput"] textarea {
            border: 2px solid #667eea !important;
            border-radius: 12px !important;
        }

        /* Button hover effects */
        .stButton button:hover {
            border-color: #667eea !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Render components
    render_ai_header_with_animation()
    render_ai_status_indicator(is_online=True)
    st.divider()
    render_ai_chat(api_url)
