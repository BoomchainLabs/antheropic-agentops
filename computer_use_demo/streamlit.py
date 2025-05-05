"""
Entrypoint for streamlit, see https://docs.streamlit.io/
"""

import asyncio
import base64
import os
import subprocess
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import cast

import streamlit as st
from anthropic import APIResponse
from anthropic.types import (
    TextBlock,
)
from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock
from streamlit.delta_generator import DeltaGenerator

from computer_use_demo.loop import (
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    APIProvider,
    sampling_loop,
)
from computer_use_demo.tools import ToolResult

CONFIG_DIR = PosixPath("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"
STREAMLIT_STYLE = """
<style>
    /* Hide chat input while agent loop is running */
    .stApp[data-teststate=running] .stChatInput textarea,
    .stApp[data-test-script-state=running] .stChatInput textarea {
        display: none;
    }
    /* Hide the streamlit deploy button */
    .stDeployButton {
        visibility: hidden;
    }
    
    /* General app styling */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Title styling */
    h1 {
        color: #7792E3;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid #7792E3;
        padding-bottom: 0.5rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(119, 146, 227, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-12oz5g7 {
        padding: 2rem 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 6px;
        border: 1px solid rgba(119, 146, 227, 0.3);
    }
    
    /* Chat input styling */
    .stChatInput>div>div>textarea {
        border-radius: 20px;
        padding: 10px 15px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 8px;
    }
    
    /* Image display */
    .stImage img {
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
"""

WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data, as malicious web content can hijack Claude's behavior"


class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"


async def setup_state():
    if "firefox" not in st.session_state:
        st.session_state.firefox = await asyncio.create_subprocess_exec(
            "firefox")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_key" not in st.session_state:
        # Try to load API key from file first, then environment
        st.session_state.api_key = os.getenv(
            "ANTHROPIC_API_KEY", ""
        )
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = st.session_state.api_key
    if "provider" not in st.session_state:
        st.session_state.provider = (
            os.getenv("API_PROVIDER", "anthropic") or APIProvider.ANTHROPIC
        )
    if "model" not in st.session_state:
        _reset_model()
    if "auth_validated" not in st.session_state:
        st.session_state.auth_validated = False
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "tools" not in st.session_state:
        st.session_state.tools = {}
    if "only_n_most_recent_images" not in st.session_state:
        st.session_state.only_n_most_recent_images = 10
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = load_from_storage("system_prompt") or ""
    if "hide_images" not in st.session_state:
        st.session_state.hide_images = False


def _reset_model():
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[
        cast(APIProvider, st.session_state.provider)
    ]


async def main():
    """Render loop for streamlit"""
    await setup_state()

    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center;'><h1>🤖 Claude Computer Use Demo</h1></div>", unsafe_allow_html=True)
    
    if not os.getenv("HIDE_WARNING", False):
        st.warning(WARNING_TEXT)
        
    st.markdown("""
        <div style='background-color: rgba(119, 146, 227, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #7792E3;'>
        <p style='margin: 0;'>Welcome to the Claude Computer Use Demo! Ask Claude to control the computer or perform tasks for you.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        def _reset_api_provider():
            if st.session_state.provider_radio != st.session_state.provider:
                _reset_model()
                st.session_state.provider = st.session_state.provider_radio
                st.session_state.auth_validated = False

        st.text_input("Model", key="model", help="The Claude model to use for this demo")
        
        st.markdown("---")
        st.markdown("### 🖼️ Image Settings")
        
        st.number_input(
            "Only send N most recent images",
            min_value=0,
            key="only_n_most_recent_images",
            help="To decrease the total tokens sent, remove older screenshots from the conversation",
        )
        
        st.checkbox("Hide screenshots", key="hide_images", 
                   help="Toggle visibility of screenshots in the conversation")
        
        st.markdown("---")
        st.markdown("### 🔧 Advanced")
        
        st.text_area(
            "Custom System Prompt Suffix",
            key="custom_system_prompt",
            help="Additional instructions to append to the system prompt. see computer_use_demo/loop.py for the base system prompt.",
            on_change=lambda: save_to_storage(
                "system_prompt", st.session_state.custom_system_prompt
            ),
        )
        
        st.markdown("---")
        if st.button("🔄 Reset Environment", type="primary", use_container_width=True):
            with st.spinner("Resetting environment..."):
                st.session_state.clear()
                setup_state()

                subprocess.run("pkill Xvfb; pkill tint2", shell=True)  # noqa: ASYNC221
                await asyncio.sleep(1)
                subprocess.run("./start_all.sh", shell=True)  # noqa: ASYNC221

    if not st.session_state.auth_validated:
        if auth_error := validate_auth(
            st.session_state.provider, st.session_state.api_key
        ):
            st.warning(f"Please resolve the following auth issue:\n\n{auth_error}")
            return
        else:
            st.session_state.auth_validated = True

    chat, http_logs = st.tabs(["💬 Chat", "🔄 HTTP Exchange Logs"])
    new_message = st.chat_input(
        "Ask Claude to control the computer..."
    )

    with chat:
        # render past chats
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    # the tool result we send back to the Anthropic API isn't sufficient to render all details,
                    # so we store the tool use responses
                    if isinstance(block, dict) and block["type"] == "tool_result":
                        _render_message(
                            Sender.TOOL, st.session_state.tools[block["tool_use_id"]]
                        )
                    else:
                        _render_message(
                            message["role"],
                            cast(BetaTextBlock | BetaToolUseBlock, block),
                        )

        # render past http exchanges
        for identity, response in st.session_state.responses.items():
            _render_api_response(response, identity, http_logs)

        # render past chats
        if new_message:
            st.session_state.messages.append(
                {
                    "role": Sender.USER,
                    "content": [TextBlock(type="text", text=new_message)],
                }
            )
            _render_message(Sender.USER, new_message)

        try:
            most_recent_message = st.session_state["messages"][-1]
        except IndexError:
            return

        if most_recent_message["role"] is not Sender.USER:
            # we don't have a user message to respond to, exit early
            return

        with st.spinner("Running Agent..."):
            # run the agent sampling loop with the newest message
            st.session_state.messages = await sampling_loop(
                system_prompt_suffix=st.session_state.custom_system_prompt,
                model=st.session_state.model,
                provider=st.session_state.provider,
                messages=st.session_state.messages,
                output_callback=partial(_render_message, Sender.BOT),
                tool_output_callback=partial(
                    _tool_output_callback, tool_state=st.session_state.tools
                ),
                api_response_callback=partial(
                    _api_response_callback,
                    tab=http_logs,
                    response_state=st.session_state.responses,
                ),
                api_key=st.session_state.api_key,
                only_n_most_recent_images=st.session_state.only_n_most_recent_images,
            )


def validate_auth(provider: APIProvider, api_key: str | None):
    if provider == APIProvider.ANTHROPIC:
        if not api_key:
            return "Enter your Anthropic API key in the sidebar to continue."


def load_from_storage(filename: str) -> str | None:
    """Load data from a file in the storage directory."""
    try:
        file_path = CONFIG_DIR / filename
        if file_path.exists():
            data = file_path.read_text().strip()
            if data:
                return data
    except Exception as e:
        st.write(f"Debug: Error loading {filename}: {e}")
    return None


def save_to_storage(filename: str, data: str) -> None:
    """Save data to a file in the storage directory."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CONFIG_DIR / filename
        file_path.write_text(data)
        # Ensure only user can read/write the file
        file_path.chmod(0o600)
    except Exception as e:
        st.write(f"Debug: Error saving {filename}: {e}")


def _api_response_callback(
    response: APIResponse[BetaMessage],
    tab: DeltaGenerator,
    response_state: dict[str, APIResponse[BetaMessage]],
):
    """
    Handle an API response by storing it to state and rendering it.
    """
    response_id = datetime.now().isoformat()
    response_state[response_id] = response
    _render_api_response(response, response_id, tab)


def _tool_output_callback(
    tool_output: ToolResult, tool_id: str, tool_state: dict[str, ToolResult]
):
    """Handle a tool output by storing it to state and rendering it."""
    tool_state[tool_id] = tool_output
    _render_message(Sender.TOOL, tool_output)


def _render_api_response(
    response: APIResponse[BetaMessage], response_id: str, tab: DeltaGenerator
):
    """Render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            st.markdown(
                f"`{response.http_request.method} {response.http_request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.http_request.headers.items())}"
            )
            st.json(response.http_request.read().decode())
            st.markdown(
                f"`{response.http_response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
            )
            st.json(response.http_response.text)


def _render_message(
    sender: Sender,
    message: str | BetaTextBlock | BetaToolUseBlock | ToolResult,
):
    """Convert input from the user or output from the agent to a streamlit message."""
    # streamlit's hotreloading breaks isinstance checks, so we need to check for class names
    is_tool_result = not isinstance(message, str) and (
        isinstance(message, ToolResult)
        or message.__class__.__name__ == "ToolResult"
        or message.__class__.__name__ == "CLIResult"
    )
    if not message or (
        is_tool_result
        and st.session_state.hide_images
        and not hasattr(message, "error")
        and not hasattr(message, "output")
    ):
        return
    
    # Set avatar and style based on sender
    avatar = None
    if sender == Sender.USER:
        avatar = "👤"
    elif sender == Sender.BOT:
        avatar = "🤖" 
    elif sender == Sender.TOOL:
        avatar = "🔧"
    
    with st.chat_message(sender, avatar=avatar):
        if is_tool_result:
            message = cast(ToolResult, message)
            
            # Handle tool output with better styling
            if message.output:
                if message.__class__.__name__ == "CLIResult":
                    st.markdown("**Terminal Output:**")
                    st.code(message.output, language="bash")
                else:
                    st.markdown(message.output)
            
            # Style errors better
            if message.error:
                st.markdown("**Error:**")
                st.error(message.error)
            
            # Improve image display with caption
            if message.base64_image and not st.session_state.hide_images:
                st.markdown("**Screenshot:**")
                st.image(
                    base64.b64decode(message.base64_image),
                    caption=f"Screenshot taken at {datetime.now().strftime('%H:%M:%S')}",
                    use_column_width=True
                )
        
        elif isinstance(message, BetaTextBlock) or isinstance(message, TextBlock):
            st.write(message.text)
        
        elif isinstance(message, BetaToolUseBlock) or isinstance(message, ToolUseBlock):
            st.markdown("**Tool Execution:**")
            st.code(f"Tool: {message.name}\nInput: {message.input}", language="json")
        
        else:
            st.markdown(message)


if __name__ == "__main__":
    asyncio.run(main())
