import uuid
from pathlib import Path
from string import Template
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from .llm import create_model, get_basic_llm_response
from .logger import logger

planner_template = Template((Path("prompts/planner.md")).read_text())
step_execution_template = Template((Path("prompts/step-execution.md")).read_text())
plan_result_template = Template((Path("prompts/plan-result.md")).read_text())


class Step(BaseModel):
    id: int
    description: str
    kubectl_command: str | None = None
    expected_output: str
    depends_on: List[int] = []


class ExecutionPlan(BaseModel):
    steps: List[Step]
    summary: str


class StepResult(BaseModel):
    step_id: int
    description: str
    result: str
    success: bool


class PlanExecutionResult(BaseModel):
    summary: str
    step_results: List[StepResult]
    total_steps: int
    successful_steps: int


def validate_plan_dependencies(plan: ExecutionPlan) -> ExecutionPlan:
    """Validate and clean up step dependencies to ensure they reference valid steps"""
    step_ids = {step.id for step in plan.steps}

    for step in plan.steps:
        original_deps = step.depends_on.copy()

        step.depends_on = [dep_id for dep_id in step.depends_on if dep_id in step_ids]

        removed_deps = [dep_id for dep_id in original_deps if dep_id not in step_ids]

        if removed_deps:
            logger.warning("Step %d (%s) had invalid dependencies removed: %s", step.id, step.description, removed_deps)

    return plan


async def create_execution_plan(question: str) -> ExecutionPlan:
    """Create a step-by-step execution plan for the user question"""
    try:
        structured_model = create_model().with_structured_output(ExecutionPlan)

        prompt_content = planner_template.substitute(question=question)

        messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content="Crie o plano de execução para esta pergunta."),
        ]

        execution_plan = await structured_model.ainvoke(messages)

        match execution_plan:
            case ExecutionPlan():
                return validate_plan_dependencies(execution_plan)
            case _:
                validated_plan = ExecutionPlan.model_validate(execution_plan)
                return validate_plan_dependencies(validated_plan)

    except Exception as e:
        logger.error("Failed to create execution plan: %s", str(e))
        fallback_plan = ExecutionPlan(
            steps=[
                Step(
                    id=1,
                    description="Diagnóstico direto da pergunta",
                    kubectl_command=None,
                    expected_output="Resposta completa",
                    depends_on=[],
                )
            ],
            summary="Execução direta sem planejamento detalhado",
        )
        return validate_plan_dependencies(fallback_plan)


async def execute_step(agent: CompiledStateGraph, step: Step, thread_id: str, previous_results: dict[int, str]) -> str:
    """Execute a single step and return the result"""
    logger.info("Executing step %d: %s", step.id, step.description)

    command_section = f"COMANDO SUGERIDO: {step.kubectl_command}" if step.kubectl_command else ""
    context_section = ""

    if step.depends_on:
        context = "\n".join(
            f"Resultado da etapa {dep_id}: {previous_results.get(dep_id, 'N/A')}" for dep_id in step.depends_on
        )

        context_section = f"CONTEXTO DAS ETAPAS ANTERIORES:\n{context}"

    step_question = step_execution_template.substitute(
        description=step.description,
        command_section=command_section,
        context_section=context_section,
    )

    result = await get_basic_llm_response(agent, step_question, f"{thread_id}_step_{step.id}_{uuid.uuid4().hex[:8]}")

    logger.info("Step %d completed", step.id)
    return result


def create_step_result(step: Step, result: str, success: bool) -> StepResult:
    """Helper to create a StepResult"""
    return StepResult(step_id=step.id, description=step.description, result=result, success=success)


def has_unsatisfied_dependencies(step: Step, results: dict[int, str]) -> bool:
    """Check if step has dependencies that aren't satisfied"""
    if not step.depends_on:
        return False

    all_dependencies_satisfied = all(dep_id in results for dep_id in step.depends_on)

    return not all_dependencies_satisfied


async def execute_plan(agent: CompiledStateGraph, plan: ExecutionPlan, thread_id: str) -> PlanExecutionResult:
    """Execute the full plan step by step"""
    logger.info("Executing plan with %d steps", len(plan.steps))

    results: dict[int, str] = {}
    step_results = []

    for step in plan.steps:
        if has_unsatisfied_dependencies(step, results):
            logger.warning("Step %d dependencies not satisfied, skipping", step.id)
            step_results.append(create_step_result(step, "Dependências não satisfeitas", False))
            continue

        try:
            result = await execute_step(agent, step, thread_id, results)
            results[step.id] = result
            step_results.append(create_step_result(step, result, True))
        except Exception as e:
            logger.error("Step %d failed: %s", step.id, str(e))
            error_msg = f"Erro na execução: {e!s}"
            results[step.id] = error_msg
            step_results.append(create_step_result(step, error_msg, False))

    return PlanExecutionResult(
        summary=plan.summary,
        step_results=step_results,
        total_steps=len(plan.steps),
        successful_steps=sum(1 for sr in step_results if sr.success),
    )


async def render_plan_result(plan_result: PlanExecutionResult) -> str:
    """Render plan execution result using template"""
    step_outputs = [
        f"{'✅' if sr.success else '❌'} **{sr.description}**\n{sr.result}" for sr in plan_result.step_results
    ]

    return plan_result_template.substitute(
        summary=plan_result.summary,
        step_outputs="\n\n".join(step_outputs),
        total_steps=plan_result.total_steps,
    )
