# api/chat.py
"""
Production Data Hub - AI Chat Endpoint

Provides natural language query interface using Google GenAI SDK.
Enhanced logging for tool call tracking and error diagnosis.

Migrated from deprecated google-generativeai to google-genai (2026-01)
Features:
- Automatic retry with exponential backoff + jitter for 429/5xx errors
- Token usage logging
- Tool call tracking
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import time
from datetime import date
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from dotenv import load_dotenv

# Add parent directory to path for shared module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import get_logger
from shared.logging_config import get_request_id

# Load Environment Variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger = get_logger(__name__)

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in .env file. AI chat will not work.")

# Initialize GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Import Tools
from .tools import (
    search_production_items,
    get_production_summary,
    get_monthly_trend,
    get_top_items,
    execute_custom_query
)

router = APIRouter(prefix="/chat", tags=["AI Chat"])


# ==========================================================
# Retry Configuration (Section 6.1)
# ==========================================================
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_TOTAL_DELAY = 15.0  # seconds
RETRYABLE_STATUS_CODES = {429, 500, 503}


# ==========================================================
# Models
# ==========================================================
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    status: str = "success"
    tools_used: List[str] = []


# ==========================================================
# System Instruction Builder (Dynamic date)
# ==========================================================
def _build_system_instruction() -> str:
    """Build system instruction with current date."""
    today = date.today()
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday_name = weekdays[today.weekday()]
    date_str = f"{today.year}년 {today.month}월 {today.day}일 {weekday_name}요일"
    current_year = today.year
    last_year = current_year - 1

    return f"""
너는 'Production Data Hub' 시스템의 전문 생산 데이터 분석가야.
사용자의 질문을 분석하여, 제공된 도구(Tools)를 사용하여 정확한 데이터를 조회하고 답변해줘.

[데이터 조회 규칙]
1. 사용자가 제품 이름(예: 'P물', '에이제품')이나 키워드로 물어보면, 반드시 `search_production_items` 도구를 먼저 사용하여 실제 제품 코드(item_code)를 확인해.
2. "작년", "{last_year}년", "단종", "예전", "과거" 같은 표현이 있으면 include_archive=True로 검색해. (기본값이 True이므로 대부분 그대로 두면 됨)
3. "올해", "최근", "현재 제품만" 같은 표현이 있으면 include_archive=False로 검색해.
4. 제품 코드를 확인한 후에만 `get_production_summary`를 사용하여 수치를 조회해.
5. 월별 추이나 기간별 흐름을 물어보면 `get_monthly_trend`를 사용해. 특정 제품의 추이가 궁금하면 item_code를 함께 넣어줘.
6. "가장 많이 생산된", "상위 제품", "순위", "랭킹" 등을 물어보면 `get_top_items`를 사용해.
7. 복잡한 조건(로트번호 패턴, 다중 필터 등)이 필요하면 `execute_custom_query`로 직접 SQL을 작성해. 사용 가능한 컬럼: production_date, item_code, item_name, good_quantity, lot_number
8. 데이터가 없으면 추측하지 말고 "조회된 데이터가 없습니다"라고 정직하게 말해.
9. 오늘 날짜는 {date_str}이야. '올해'는 {current_year}년, '작년'은 {last_year}년을 의미해.

[답변 스타일]
- 친절하고 전문적인 어조를 사용해.
- 수치 데이터에는 반드시 단위(개, 건 등)를 붙여줘.
- 답변의 근거가 된 조회 기간을 명확히 명시해.
"""


def _is_retryable_error(e: Exception) -> tuple[bool, int]:
    """
    Check if the error is retryable.
    Returns (is_retryable, status_code).
    """
    status_code = 0

    if isinstance(e, (ClientError, ServerError)):
        status_code = getattr(e, 'status', 0) or 0
        # Extract status code from error message if not in attribute
        if status_code == 0:
            error_msg = str(e)
            for code in RETRYABLE_STATUS_CODES:
                if str(code) in error_msg:
                    status_code = code
                    break

        if status_code in RETRYABLE_STATUS_CODES:
            return True, status_code

    return False, status_code


def _calculate_delay(attempt: int) -> float:
    """
    Calculate delay with exponential backoff + jitter.
    Formula: min(base * 2^attempt + random_jitter, max_delay)
    """
    exponential = BASE_DELAY * (2 ** attempt)
    jitter = random.uniform(0, 1)  # Add 0-1 second random jitter
    delay = min(exponential + jitter, MAX_TOTAL_DELAY / MAX_RETRIES)
    return delay


@router.post("/", response_model=ChatResponse)
async def chat_with_data(request: ChatRequest):
    """
    Process natural language query using Gemini AI with tool calling.
    Includes automatic retry with exponential backoff for transient errors.
    """
    request_id = get_request_id()
    start_time = time.perf_counter()

    if not client:
        logger.error(f"[Chat] request_id={request_id} | API key not configured")
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured.")

    # Log incoming request
    query_preview = request.query[:100] + "..." if len(request.query) > 100 else request.query
    logger.info(f"[Chat Request] request_id={request_id} | query='{query_preview}'")

    # Build dynamic system instruction
    system_instruction = _build_system_instruction()

    # Retry loop
    last_error = None
    total_delay = 0.0

    for attempt in range(MAX_RETRIES):
        try:
            # Generate content with tools and system instruction
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=request.query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[
                        search_production_items,
                        get_production_summary,
                        get_monthly_trend,
                        get_top_items,
                        execute_custom_query
                    ],
                ),
            )

            # Success - extract tools and return
            tools_used, tool_calls_detail = _extract_tool_info(response, request_id)
            duration_ms = (time.perf_counter() - start_time) * 1000
            token_info = _log_token_usage(response, request_id)

            # Log response
            if not tools_used:
                logger.warning(
                    f"[Chat Response] request_id={request_id} | "
                    f"NO TOOLS USED - potential hallucination | "
                    f"query='{query_preview}' | {token_info} | duration_ms={duration_ms:.1f}"
                )
            else:
                logger.info(
                    f"[Chat Response] request_id={request_id} | "
                    f"tools_used={tools_used} | "
                    f"tool_calls={tool_calls_detail} | "
                    f"{token_info} | duration_ms={duration_ms:.1f}"
                )

            return ChatResponse(
                answer=response.text,
                tools_used=tools_used
            )

        except (ClientError, ServerError) as e:
            last_error = e
            is_retryable, status_code = _is_retryable_error(e)

            if is_retryable and attempt < MAX_RETRIES - 1:
                delay = _calculate_delay(attempt)
                total_delay += delay

                # Check if we've exceeded total delay budget
                if total_delay > MAX_TOTAL_DELAY:
                    logger.warning(
                        f"[Chat Retry] request_id={request_id} | "
                        f"Total delay budget exceeded ({total_delay:.1f}s > {MAX_TOTAL_DELAY}s). Giving up."
                    )
                    break

                logger.warning(
                    f"[Chat Retry] request_id={request_id} | "
                    f"status={status_code} | attempt={attempt+1}/{MAX_RETRIES} | "
                    f"delay={delay:.1f}s | error={e}"
                )
                await asyncio.sleep(delay)
            else:
                # Non-retryable or last attempt
                break

        except Exception as e:
            # Non-API errors - don't retry
            last_error = e
            break

    # All retries exhausted or non-retryable error
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Log full exception with stack trace
    logger.exception(
        f"[Chat Error] request_id={request_id} | "
        f"query='{query_preview}' | "
        f"error={type(last_error).__name__}: {last_error} | "
        f"duration_ms={duration_ms:.1f}"
    )

    # Provide helpful error message based on error type
    error_message = _get_user_friendly_error(last_error)

    return ChatResponse(
        answer=error_message,
        status="error"
    )


def _extract_tool_info(response, request_id: str) -> tuple[List[str], List[str]]:
    """Extract tool usage information from response."""
    tools_used = []
    tool_calls_detail = []

    try:
        # Check candidates for function calls
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_name = part.function_call.name
                            if tool_name not in tools_used:
                                tools_used.append(tool_name)
                                args = dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                                tool_calls_detail.append(f"{tool_name}({args})")

        # Check automatic_function_calling_history
        if hasattr(response, 'automatic_function_calling_history'):
            for entry in response.automatic_function_calling_history:
                if hasattr(entry, 'parts'):
                    for part in entry.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_name = part.function_call.name
                            if tool_name not in tools_used:
                                tools_used.append(tool_name)
                                args = dict(part.function_call.args) if hasattr(part.function_call, 'args') else {}
                                tool_calls_detail.append(f"{tool_name}({args})")

    except (IndexError, AttributeError, TypeError) as e:
        logger.warning(
            f"[Chat] request_id={request_id} | "
            f"Failed to extract tool info: {type(e).__name__}: {e}"
        )

    return tools_used, tool_calls_detail


def _log_token_usage(response, request_id: str) -> str:
    """Log and return token usage info."""
    token_info = ""
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        um = response.usage_metadata
        prompt_tokens = getattr(um, 'prompt_token_count', 0)
        response_tokens = getattr(um, 'candidates_token_count', 0)
        total_tokens = getattr(um, 'total_token_count', 0)
        token_info = f"tokens(prompt={prompt_tokens}, response={response_tokens}, total={total_tokens})"
        logger.info(f"[Token Usage] request_id={request_id} | {token_info}")
    return token_info


def _get_user_friendly_error(e: Exception) -> str:
    """Return user-friendly error message based on error type."""
    error_str = str(e)

    if isinstance(e, ClientError):
        if '429' in error_str or 'quota' in error_str.lower():
            return (
                "죄송합니다. 현재 AI 서비스 사용량이 한도에 도달했습니다. "
                "잠시 후 다시 시도해 주세요. "
                "(무료 API 일일 한도 초과일 수 있습니다)"
            )
        elif '401' in error_str or '403' in error_str:
            return "AI 서비스 인증에 문제가 발생했습니다. 관리자에게 문의해 주세요."

    if isinstance(e, ServerError):
        return (
            "AI 서비스가 일시적으로 불안정합니다. "
            "잠시 후 다시 시도해 주세요."
        )

    return f"죄송합니다. 질문을 처리하는 중에 오류가 발생했습니다: {str(e)}"
