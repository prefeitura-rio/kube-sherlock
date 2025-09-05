from dataclasses import dataclass, field
from string import Template
from typing import Annotated, Type, TypedDict, TypeVar, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from .constants import EvaluationDecision, WorkflowDecision
from .errors import AgentErrorMessages
from .llm import create_model
from .logger import logger
from .settings import settings
from .templates import load_prompt_template, load_prompt_text

T = TypeVar("T", bound=BaseModel)


@tool
def human_assistance(request: str) -> str:
    """Request human assistance when needed"""
    human_response = interrupt({"query": request})
    return human_response["data"]


class TaskPlan(BaseModel):
    """Structured plan for the worker agent"""

    task_description: str = Field(
        min_length=10, max_length=1000, description="Specific, actionable task description - not generic"
    )
    expected_outcome: str = Field(min_length=5, max_length=500, description="Concrete expected result")
    kubectl_commands: list[str] = Field(
        default_factory=list, description="Specific kubectl commands relevant to the task"
    )
    verification_steps: list[str] = Field(
        default_factory=list, description="Steps to verify the task was completed correctly"
    )


class EvaluationResponse(BaseModel):
    """Structured evaluation response from the supervisor"""

    decision: EvaluationDecision
    feedback: str = ""


class SupervisorState(TypedDict):
    """State for the supervisor-worker workflow"""

    messages: Annotated[list, add_messages]
    original_question: str
    current_plan: TaskPlan | None
    worker_result: str
    evaluation: str
    feedback: str
    iteration_count: int
    max_iterations: int
    final_response: str
    main_thread_id: str


@dataclass
class SupervisorWorkerSystem:
    """Supervisor-Worker agent system with feedback loops"""

    store: BaseStore
    checkpointer: BaseCheckpointSaver
    input_tools: list[BaseTool]
    workflow: CompiledStateGraph = field(init=False)
    supervisor_model: BaseChatModel = field(default_factory=create_model)
    worker_model: BaseChatModel = field(default_factory=create_model)
    supervisor_prompt: str = field(default_factory=lambda: load_prompt_text("supervisor.md"))
    worker_prompt: str = field(default_factory=lambda: load_prompt_text("worker.md"))
    evaluation_prompt: str = field(default_factory=lambda: load_prompt_text("evaluation.md"))
    plan_creation_template: Template = field(default_factory=lambda: load_prompt_template("plan-creation.md"))
    plan_refinement_template: Template = field(default_factory=lambda: load_prompt_template("plan-refinement.md"))
    task_execution_template: Template = field(default_factory=lambda: load_prompt_template("task-execution.md"))
    evaluation_context_template: Template = field(default_factory=lambda: load_prompt_template("evaluation-context.md"))

    def __post_init__(self) -> None:
        self.tools = [*self.input_tools, human_assistance]
        self.workflow = self.build_workflow()

    async def invoke_model(
        self,
        model: BaseChatModel,
        system_prompt: str,
        user_prompt: str,
        config: RunnableConfig | None = None,
        *,
        bind_tools: bool = False,
    ) -> str:
        """Helper method to invoke models with or without tools"""
        if bind_tools:
            model_with_tools = model.bind_tools(self.tools)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = await model_with_tools.ainvoke(messages, config=config)

            logger.info(f"Model response type: {type(response)}")
            logger.info(f"Response content: {response.content}")
            logger.info(f"Response has tool_calls: {hasattr(response, 'tool_calls')}")

            if hasattr(response, "tool_calls"):
                logger.info(f"Tool calls: {response.tool_calls}")
        else:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = await model.ainvoke(messages, config=config)

        match response.content:
            case str(content):
                return content
            case list(content):
                return " ".join(str(item) for item in content).strip()

    async def invoke_structured_model(
        self,
        model: BaseChatModel,
        model_type: Type[T],
        system_prompt: str,
        user_prompt: str,
        config: RunnableConfig | None = None,
    ) -> T:
        """Helper method to invoke structured models with consistent pattern"""
        structured_model = model.with_structured_output(model_type)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        return cast(T, await structured_model.ainvoke(messages, config=config))

    def build_workflow(self) -> CompiledStateGraph:
        """Build the supervisor-worker workflow graph"""
        workflow = StateGraph(SupervisorState)

        workflow.add_node("create_plan", self.create_plan_node)
        workflow.add_node("execute_task", self.execute_task_node)
        workflow.add_node("evaluate_result", self.evaluate_result_node)
        workflow.add_node("finalize", self.finalize_node)

        workflow.set_entry_point("create_plan")

        workflow.add_edge("create_plan", "execute_task")
        workflow.add_edge("execute_task", "evaluate_result")

        workflow.add_conditional_edges(
            "evaluate_result",
            self.should_continue,
            {WorkflowDecision.CONTINUE.value: "create_plan", WorkflowDecision.FINALIZE.value: "finalize"},
        )

        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def create_plan_node(self, state: SupervisorState) -> dict:
        """Supervisor creates/refines task plan"""
        iteration = state.get("iteration_count", 0)

        match iteration:
            case 0:
                prompt = self.plan_creation_template.substitute(question=state["original_question"])
            case _:
                prompt = self.plan_refinement_template.substitute(
                    question=state["original_question"],
                    previous_plan=state["current_plan"].task_description if state["current_plan"] else "Nenhum",
                    previous_result=state.get("worker_result", "Nenhum"),
                    feedback=state.get("feedback", "Nenhum"),
                )

        try:
            plan_response = await self.invoke_structured_model(
                self.supervisor_model,
                TaskPlan,
                self.supervisor_prompt,
                prompt,
            )

            logger.info(f"Plan created (iteration {iteration + 1}): {plan_response.task_description}")
            return {"current_plan": plan_response, "iteration_count": iteration + 1}
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")

            question_lower = state["original_question"].lower()
            if "pod" in question_lower:
                commands = ["kubectl get pods --all-namespaces", "kubectl describe pods"]
                outcome = "List and describe pod status and issues"
            elif "service" in question_lower:
                commands = ["kubectl get services --all-namespaces", "kubectl describe services"]
                outcome = "Analyze service configuration and endpoints"
            elif "namespace" in question_lower:
                commands = ["kubectl get namespaces", "kubectl describe namespaces"]
                outcome = "Review namespace configuration and resource quotas"
            else:
                commands = [
                    "kubectl cluster-info",
                    "kubectl get nodes",
                    "kubectl get pods --all-namespaces --show-labels",
                ]
                outcome = "Gather cluster overview and identify potential issues"

            fallback_plan = TaskPlan(
                task_description=(
                    f"Intelligent diagnostic analysis for: {state['original_question']} "
                    f"(fallback mode due to planning error: {str(e)[:50]})"
                ),
                expected_outcome=outcome,
                kubectl_commands=commands,
                verification_steps=[
                    "Verify commands executed successfully",
                    "Check output contains real data, not placeholder text",
                    "Ensure response addresses the original question",
                ],
            )

            return {"current_plan": fallback_plan, "iteration_count": iteration + 1}

    async def execute_task_node(self, state: SupervisorState) -> dict:
        """Worker agent executes the planned task"""
        plan = state["current_plan"]

        if not plan:
            return {"worker_result": "Error: Plan was not created"}

        commands = "\n".join(f"- {cmd}" for cmd in plan.kubectl_commands)
        steps = "\n".join(f"- {step}" for step in plan.verification_steps)

        task_prompt = self.task_execution_template.substitute(
            task_description=plan.task_description,
            commands=commands,
            expected_outcome=plan.expected_outcome,
            verification_steps=steps,
        )

        try:
            main_thread_id = state["main_thread_id"]
            config = RunnableConfig(configurable={"thread_id": main_thread_id})

            logger.info(f"Worker executing with prompt: {task_prompt[:200]}...")
            logger.info(f"Available tools count: {len(self.tools)}")

            for tool in self.tools:
                logger.info(f"  Tool: {tool.name}")

            worker_response = await self.invoke_model(
                self.worker_model,
                self.worker_prompt,
                task_prompt,
                config,
                bind_tools=True,
            )

            logger.info(f"Worker completed: {len(worker_response)} chars")
            logger.info(f"Worker response: {worker_response[:500]}...")

            return {"worker_result": worker_response}
        except Exception as e:
            logger.error(f"Worker execution failed: {e}")
            return {"worker_result": f"Error: {e}"}

    async def evaluate_result_node(self, state: SupervisorState) -> dict:
        """Supervisor evaluates worker result"""
        plan_description = state["current_plan"].task_description if state["current_plan"] else "No plan"

        evaluation_text = self.evaluation_context_template.substitute(
            original_question=state["original_question"],
            plan_description=plan_description,
            worker_result=state["worker_result"],
        )

        try:
            evaluation_response = await self.invoke_structured_model(
                self.supervisor_model,
                EvaluationResponse,
                self.evaluation_prompt,
                evaluation_text,
            )

            logger.info(f"Evaluation: {evaluation_response.decision}")

            return {"evaluation": evaluation_response.decision, "feedback": evaluation_response.feedback}
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "evaluation": EvaluationDecision.REFINE.value,
                "feedback": (
                    f"Evaluation system failed - please retry with more specific information. Error: {str(e)[:100]}"
                ),
            }

    async def finalize_node(self, state: SupervisorState) -> dict:
        """Finalize the workflow with the approved response"""
        return {"final_response": state["worker_result"]}

    def should_continue(self, state: SupervisorState) -> str:
        """Determine whether to continue iterating, get human review, or finalize"""
        max_iterations = state.get("max_iterations", settings.REFLECTION_ITERATIONS)
        current_iteration = state.get("iteration_count", 0)
        evaluation = state.get("evaluation", "")

        match (evaluation, current_iteration >= max_iterations):
            case (eval_val, _) if eval_val == EvaluationDecision.APPROVED.value:
                return WorkflowDecision.FINALIZE.value
            case (_, True):
                return WorkflowDecision.FINALIZE.value
            case _:
                return WorkflowDecision.CONTINUE.value

    async def process_question(self, question: str, thread_id: str) -> str:
        """Process a question through the supervisor-worker workflow"""

        initial_state = SupervisorState(
            messages=[HumanMessage(content=question)],
            original_question=question,
            current_plan=None,
            worker_result="",
            evaluation="",
            feedback="",
            iteration_count=0,
            max_iterations=settings.REFLECTION_ITERATIONS,
            final_response="",
            main_thread_id=thread_id,
        )

        try:
            workflow = self.workflow

            config = RunnableConfig(configurable={"thread_id": thread_id})
            final_state = await workflow.ainvoke(initial_state, config)

            response = final_state.get("final_response", "")

            if not response:
                return AgentErrorMessages.PROCESSING_REQUEST.value

            iterations = final_state.get("iteration_count", 0)
            logger.info(f"Completed in {iterations} iterations")

            return response

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return AgentErrorMessages.PROCESSING_REQUEST.value
