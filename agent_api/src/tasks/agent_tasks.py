"""Celery tasks for background processing."""

import asyncio
from typing import Any

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from agents import get_agent
from core.celery_app import app
from api.utils import langchain_to_chat_message


@app.task(bind=True, max_retries=3)
def invoke_agent_async(
    self,
    agent_id: str,
    message: str,
    thread_id: str,
    user_id: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Invoke agent asynchronously in a Celery worker.

    Args:
        agent_id: The agent to invoke
        message: User message
        thread_id: Thread ID for conversation persistence
        user_id: User ID
        model: Optional model override

    Returns:
        Dict with status and response
    """
    try:
        agent = get_agent(agent_id)

        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig

        configurable = {"thread_id": thread_id, "user_id": user_id}
        if model:
            configurable["model"] = model

        config = RunnableConfig(configurable=configurable)

        # Run the async agent in the sync Celery task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response_events = loop.run_until_complete(
                agent.ainvoke(
                    {"messages": [HumanMessage(content=message)]},
                    config=config,
                    stream_mode=["updates", "values"],
                )
            )

            response_type, response = response_events[-1]

            if response_type == "values":
                output = langchain_to_chat_message(response["messages"][-1])
                return {
                    "status": "success",
                    "message": output.model_dump(),
                }
            else:
                return {
                    "status": "error",
                    "message": "Unexpected response type",
                }
        finally:
            loop.close()

    except Exception as exc:
        try:
            self.retry(countdown=60, exc=exc)
        except MaxRetriesExceededError:
            return {
                "status": "error",
                "message": str(exc),
            }


@app.task
def cleanup_expired_sessions() -> dict[str, int]:
    """Periodic task to cleanup expired sessions.

    Returns:
        Dict with count of cleaned sessions
    """
    # Placeholder for session cleanup logic
    # In a real implementation, this would query the database
    # and remove old/stale sessions
    return {"cleaned_sessions": 0}


@app.task
def send_notification(user_id: str, message: str) -> dict[str, Any]:
    """Send notification to a user.

    Args:
        user_id: Target user ID
        message: Notification message

    Returns:
        Dict with status
    """
    # Placeholder for notification logic
    # Could integrate with email, push notifications, etc.
    return {
        "status": "success",
        "user_id": user_id,
        "message": message,
    }


@app.task
def process_document_ingestion(file_path: str, user_id: str) -> dict[str, Any]:
    """Process document ingestion in background.

    Args:
        file_path: Path to the document file
        user_id: User who initiated the ingestion

    Returns:
        Dict with ingestion results
    """
    # Placeholder for document processing logic
    # This would use the existing ingest.py functionality
    return {
        "status": "success",
        "file_path": file_path,
        "chunks_processed": 0,
    }
