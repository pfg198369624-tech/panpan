import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.session import AnalysisSession
from app.models.workflow_log import WorkflowLog
from app.services.collector import collector
from app.services.cleaner import cleaner
from app.services.single_pass import single_pass
from app.services.prd_generator import prd_generator
from app.services.test_generator import test_generator
from app.services.validator import validator as validator_svc
from app.workflow.reflection import ReflectionEngine
from app.workflow.websocket import ws_manager
from app.workflow.steps import step_descriptions
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def _log_step(db: Session, session_id: str, step: str, status: str,
                    input_summary: str = "", output_summary: str = "",
                    error_message: str = ""):
    log = WorkflowLog(
        session_id=session_id,
        step=step,
        status=status,
        input_summary=input_summary[:500],
        output_summary=output_summary[:500],
        error_message=error_message[:500] if error_message else None,
        started_at=datetime.now() if status == "running" else None,
        finished_at=datetime.now() if status != "running" else None,
    )
    db.add(log)
    db.commit()


async def run_workflow(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found")
            return

        session.status = "running"
        session.started_at = datetime.now()
        db.commit()

        reflection = ReflectionEngine(session_id)
        total_steps = settings.workflow_total_steps

        for step_num in range(1, total_steps + 1):
            if session.status == "no_data" and step_num > 2:
                await ws_manager.push_step(session_id, step_num, "skipped",
                                           "跳过: 无可用评论数据")
                await _log_step(db, session_id, str(step_num), "skipped",
                               error_message="无数据，跳过后续步骤")
                continue

            session.current_step = step_num
            db.commit()

            desc = step_descriptions.get(step_num, f"Step {step_num}")
            await ws_manager.push_step(session_id, step_num, "running", desc)
            await _log_step(db, session_id, str(step_num), "running", input_summary=desc)

            max_attempts = settings.workflow_max_retry_per_step
            success = False
            step_output = {}

            for attempt in range(max_attempts):
                try:
                    if step_num == 1:
                        scope = await _run_scope(db, session)
                        step_output = {"scope": scope}
                        success = True

                    elif step_num == 2:
                        from app.models.review import ReviewRaw
                        from sqlalchemy import text as sa_text
                        db.commit()
                        existing_orm = db.query(ReviewRaw).filter(ReviewRaw.session_id == session_id).count()
                        existing_raw = db.execute(sa_text("SELECT COUNT(*) FROM reviews_raw WHERE session_id = :sid"), {"sid": session_id}).scalar()
                        if existing_orm > 0 or existing_raw > 0:
                            count = max(existing_orm, existing_raw)
                            step_output = {
                                "count": count,
                                "data_notes": ["使用已有数据（跳过采集）"],
                            }
                            success = True
                        else:
                            collect_result = await collector.collect(db, session_id, session.app_url)
                            count = collect_result["count"]
                            if count == 0:
                                notes = "; ".join(collect_result.get("data_notes", []))
                                logger.warning(f"Session {session_id}: 零条数据. {notes}")
                                step_output = {
                                    "count": 0,
                                    "data_notes": collect_result.get("data_notes", []),
                                    "error": "US App Store RSS 未返回评论数据。可尝试通过 JSON/CSV 导入数据。",
                                }
                                session.status = "no_data"
                                session.error_message = step_output["error"]
                                db.commit()
                                success = True
                            else:
                                step_output = {
                                    "count": count,
                                    "pages_fetched": collect_result.get("pages_fetched", 0),
                                    "first_review_date": collect_result.get("first_review_date"),
                                    "last_review_date": collect_result.get("last_review_date"),
                                    "data_notes": collect_result.get("data_notes", []),
                                }
                                success = True

                    elif step_num == 3:
                        count = await cleaner.clean(db, session_id)
                        step_output = {"count": count, "noise_ratio": 0}
                        success = True

                    elif step_num == 4:
                        result = await single_pass.analyze(db, session_id, session.user_goal or "")
                        step_output = result
                        success = result["classifications"] > 0 and result["findings"] > 0

                    elif step_num == 5:
                        p_count = await prd_generator.generate(db, session_id)
                        step_output = {"requirements": p_count}
                        success = True

                    elif step_num == 6:
                        t_count = await test_generator.generate(db, session_id)
                        step_output = {"test_cases": t_count}
                        success = True

                    elif step_num == 7:
                        report = validator_svc.validate_traceability(db, session_id)
                        step_output = {
                            "issues": len(report["issues"]),
                            "revisions": len(report["revisions"]),
                        }
                        success = True

                except Exception as e:
                    logger.error(f"Step {step_num} attempt {attempt + 1} failed: {e}")
                    step_output = {"error": str(e)}
                    continue

                if session.status == "no_data":
                    break

                reflect_result = reflection.reflect(step_num, step_output)
                if reflect_result["passed"]:
                    break
                else:
                    logger.warning(f"Reflection failed for step {step_num}: {reflect_result['reason']}")
                    if not reflect_result["should_retry"] or attempt >= max_attempts - 1:
                        break

            if success:
                await ws_manager.push_step(session_id, step_num, "success",
                                           f"{desc} completed")
                await _log_step(db, session_id, str(step_num), "success",
                               output_summary=str(step_output))
            else:
                await ws_manager.push_step(session_id, step_num, "failed",
                                           f"{desc} failed after {max_attempts} attempts")
                await _log_step(db, session_id, str(step_num), "failed",
                               error_message=str(step_output.get("error", "Unknown error")))

        if session.status != "no_data":
            session.status = "success"
        session.finished_at = datetime.now()
        if session.started_at:
            session.duration_seconds = int((session.finished_at - session.started_at).total_seconds())
        db.commit()

        await ws_manager.push(session_id, {
            "type": "workflow_complete",
            "status": session.status,
        })

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if session:
            session.status = "failed"
            session.error_message = str(e)
            session.finished_at = datetime.now()
            db.commit()
        await ws_manager.push(session_id, {"type": "workflow_complete", "status": "failed"})

    finally:
        db.close()


async def _run_scope(db, session):
    from app.core.prompt_manager import prompt_manager
    from app.services.ai_client import ai_client
    from app.schemas.validator import AIOutputValidator
    import json

    if not session.user_goal:
        return {"scope_description": "全量分析所有用户评论", "data_requirements": "iTunes RSS Feed"}

    prompt = f"""分析以下分析目标并确定分析范围:
目标: {session.user_goal}
App链接: {session.app_url}

输出JSON格式:
{{"scope_description": "分析范围描述", "data_requirements": "所需数据说明"}}"""

    result = await ai_client.call(prompt, task="scope")
    if result.success:
        try:
            data = json.loads(AIOutputValidator.repair_json(result.text))
            return data
        except Exception:
            pass
    return {"scope_description": session.user_goal, "data_requirements": "iTunes RSS Feed"}
