from langgraph.graph import StateGraph, END
from state import FilmProductionState
from agents import researcher_agent, writing_team_agent, review_team_agent, should_revise
from langchain_groq import ChatGroq
import os

def create_film_production_workflow(use_llm=True, groq_api_key=None, tavily_api_key=None, model_name="llama-3.3-70b-versatile"):
    llm = None
    
    if use_llm:
        if not groq_api_key or groq_api_key.strip() == "":
            print("Warning: No Groq API key provided. Using simulated mode.")
            use_llm = False
        else:
            os.environ["GROQ_API_KEY"] = groq_api_key
            
            try:
                llm = ChatGroq(
                    model=model_name,
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=60,
                    max_retries=2,
                )
                test_response = llm.invoke("test")
                print("Groq LLM initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Groq: {e}")
                print("Falling back to simulated mode")
                llm = None
    
    workflow = StateGraph(FilmProductionState)
    
    workflow.add_node("researcher", lambda state: researcher_agent(state, llm, tavily_api_key))
    workflow.add_node("writing_team", lambda state: writing_team_agent(state, llm))
    workflow.add_node("review_team", lambda state: review_team_agent(state, llm))
    
    workflow.set_entry_point("researcher")
    
    workflow.add_edge("researcher", "writing_team")
    workflow.add_edge("writing_team", "review_team")
    
    workflow.add_conditional_edges(
        "review_team",
        should_revise,
        {
            "needs_revision": "writing_team",
            "approved": END
        }
    )
    
    return workflow.compile()


def generate_workflow_graph(output_path="workflow_graph.png"):
    from IPython.display import Image, display
    
    workflow = StateGraph(FilmProductionState)
    
    workflow.add_node("researcher", lambda state: state)
    workflow.add_node("writing_team", lambda state: state)
    workflow.add_node("review_team", lambda state: state)
    
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "writing_team")
    workflow.add_edge("writing_team", "review_team")
    workflow.add_conditional_edges(
        "review_team",
        should_revise,
        {
            "needs_revision": "writing_team",
            "approved": END
        }
    )
    
    graph = workflow.compile()
    
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"Workflow graph saved to {output_path}")
        return Image(png_data)
    except Exception as e:
        print(f"Could not generate graph: {e}")
        return None


def run_workflow(topic: str, use_llm=True, groq_api_key=None, tavily_api_key=None, model_name="llama-3.3-70b-versatile"):
    initial_state = FilmProductionState(
        topic=topic,
        research_findings="",
        script="",
        rating=0,
        feedback="",
        iteration=0
    )
    
    workflow = create_film_production_workflow(use_llm, groq_api_key, tavily_api_key, model_name)
    
    results = []
    for state in workflow.stream(initial_state):
        results.append(state)
    
    if results:
        last_key = list(results[-1].keys())[-1]
        return results[-1][last_key]
    
    return None