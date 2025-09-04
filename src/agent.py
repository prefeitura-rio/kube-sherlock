from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore
from pydantic import BaseModel

from .errors import AgentErrorMessages
from .llm import create_model
from .logger import logger
from .settings import settings
from .templates import load_prompt_template, load_prompt_text
from .utils import extract_response_content


class TaskPlan(BaseModel):
    """Structured plan for the worker agent"""

    task_description: str
    expected_outcome: str
    kubectl_commands: list[str] = []
    verification_steps: list[str] = []


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


class SupervisorWorkerSystem:
    """Supervisor-Worker agent system with feedback loops"""

    def __init__(self, store: BaseStore, checkpointer: BaseCheckpointSaver, tools: list[BaseTool]):
        self.store = store
        self.checkpointer = checkpointer
        self.tools = tools
        self.supervisor_model = create_model()
        self.worker_agent = None
        self.workflow = None
        self.supervisor_prompt = load_prompt_text("supervisor.md")
        self.worker_prompt = load_prompt_text("worker.md")
        self.evaluation_prompt = load_prompt_text("evaluation.md")
        self.plan_creation_template = load_prompt_template("plan-creation.md")
        self.plan_refinement_template = load_prompt_template("plan-refinement.md")
        self.task_execution_template = load_prompt_template("task-execution.md")
        self.evaluation_context_template = load_prompt_template("evaluation-context.md")

    async def initialize(self):
        """Initialize the supervisor-worker system"""
        logger.info("Initializing supervisor-worker system...")

        self.worker_agent = create_react_agent(
            model=self.supervisor_model,
            prompt=self.worker_prompt,
            tools=self.tools,
            store=self.store,
        )

        self.workflow = self.build_workflow()

        logger.info("Supervisor-worker system initialized successfully")

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
            {"continue": "create_plan", "finalize": "finalize"},
        )

        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def create_plan_node(self, state: SupervisorState) -> dict:
        """Supervisor creates/refines task plan"""
        iteration = state.get("iteration_count", 0)

        if iteration == 0:
            prompt = self.plan_creation_template.substitute(question=state["original_question"])
        else:
            prompt = self.plan_refinement_template.substitute(
                question=state["original_question"],
                previous_plan=state["current_plan"].task_description if state["current_plan"] else "Nenhum",
                previous_result=state.get("worker_result", "Nenhum"),
                feedback=state.get("feedback", "Nenhum"),
            )

        structured_model = self.supervisor_model.with_structured_output(TaskPlan)

        messages = [SystemMessage(content=self.supervisor_prompt), HumanMessage(content=prompt)]

        try:
            plan = await structured_model.ainvoke(messages)
            logger.info(f"Plan created (iteration {iteration + 1}): {plan.task_description}")

            return {"current_plan": plan, "iteration_count": iteration + 1}
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")

            fallback_plan = TaskPlan(
                task_description=f"Direct diagnosis: {state['original_question']}",
                expected_outcome="Complete response",
                kubectl_commands=["kubectl get pods", "kubectl get namespaces"],
                verification_steps=["Verify completeness"],
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
            if not self.worker_agent:
                raise RuntimeError("Worker agent not initialized")

            main_thread_id = state["main_thread_id"]
            config = RunnableConfig(configurable={"thread_id": main_thread_id})

            result = await self.worker_agent.ainvoke({"messages": [HumanMessage(content=task_prompt)]}, config=config)

            worker_result = extract_response_content({"structured_response": result})
            logger.info(f"Worker completed: {len(worker_result)} chars")

            return {"worker_result": worker_result}
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

        messages = [SystemMessage(content=self.evaluation_prompt), HumanMessage(content=evaluation_text)]

        try:
            response = await self.supervisor_model.ainvoke(messages)
            evaluation = str(response.content).strip()

            if "APROVADO" in evaluation:
                logger.info(f"Approved after {state['iteration_count']} iterations")
                return {"evaluation": "APROVADO", "feedback": ""}
            elif "REFINAR:" in evaluation:
                feedback = evaluation.split("REFINAR:")[1].strip()
                logger.info(f"Needs refinement: {feedback[:50]}...")
                return {"evaluation": "REFINAR", "feedback": feedback}
            else:
                logger.warning(f"Unclear evaluation: {evaluation[:50]}")
                return {"evaluation": "APROVADO", "feedback": ""}
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"evaluation": "APROVADO", "feedback": ""}

    async def finalize_node(self, state: SupervisorState) -> dict:
        """Finalize the workflow with the approved response"""
        return {"final_response": state["worker_result"]}

    def should_continue(self, state: SupervisorState) -> Literal["continue", "finalize"]:
        """Determine whether to continue iterating or finalize"""
        max_iterations = state.get("max_iterations", settings.REFLECTION_ITERATIONS)
        current_iteration = state.get("iteration_count", 0)
        evaluation = state.get("evaluation", "")

        if evaluation == "APROVADO" or current_iteration >= max_iterations:
            return "finalize"

        return "continue"

    async def process_question(self, question: str, thread_id: str) -> str:
        """Process a question through the supervisor-worker workflow"""
        if not self.workflow:
            await self.initialize()

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
            if not self.workflow:
                raise RuntimeError("Workflow not initialized")

            config = RunnableConfig(configurable={"thread_id": thread_id})
            final_state = await self.workflow.ainvoke(initial_state, config)

            response = final_state.get("final_response", "")

            if not response:
                return AgentErrorMessages.PROCESSING_REQUEST.value

            iterations = final_state.get("iteration_count", 0)
            logger.info(f"Completed in {iterations} iterations")

            return response

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return AgentErrorMessages.PROCESSING_REQUEST.value


async def create_supervisor_worker_system(
    store: BaseStore, checkpointer: BaseCheckpointSaver, tools: list[BaseTool]
) -> SupervisorWorkerSystem:
    """Create and initialize the supervisor-worker system"""
    system = SupervisorWorkerSystem(store, checkpointer, tools)

    await system.initialize()

    return system
