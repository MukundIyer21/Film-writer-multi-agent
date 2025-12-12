import streamlit as st
from datetime import datetime
import json
from workflow import create_film_production_workflow
from state import FilmProductionState
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Film Production Studio",
    layout="wide"
)

if 'workflow_complete' not in st.session_state:
    st.session_state.workflow_complete = False
if 'final_results' not in st.session_state:
    st.session_state.final_results = None
if 'all_iterations' not in st.session_state:
    st.session_state.all_iterations = []

st.title("AI Film Production Studio")
st.subheader("Research → Script → Review (Auto-Revision if Rating < 7)")

groq_api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
tavily_api_key = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))

use_llm = True
model_name = "llama-3.3-70b-versatile"

tab1, tab2 = st.tabs(["Create Production", "Results"])

with tab1:
    st.subheader("New Film Concept")
    
    topic = st.text_input(
        "Film Topic",
        placeholder="e.g., Artificial Intelligence Ethics"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("Start Pipeline", type="primary", use_container_width=True)
    with col2:
        reset_btn = st.button("Reset", use_container_width=True)
    
    if reset_btn:
        st.session_state.workflow_complete = False
        st.session_state.final_results = None
        st.session_state.all_iterations = []
        st.rerun()
    
    if start_btn and topic:
        if not groq_api_key or not groq_api_key.strip():
            st.error("Groq API key not configured. Please contact the administrator.")
        else:
            st.divider()
            st.subheader("Pipeline Progress")
            
            progress_bar = st.progress(0)
            status_container = st.empty()
            output_container = st.container()
            
            initial_state = FilmProductionState(
                topic=topic,
                research_findings="",
                script="",
                rating=0,
                feedback="",
                iteration=0
            )
            
            try:
                workflow = create_film_production_workflow(use_llm, groq_api_key, tavily_api_key, model_name)
                
                st.session_state.all_iterations = []
                total_steps = 0
                
                for state_update in workflow.stream(initial_state):
                    node_name = list(state_update.keys())[0]
                    current_state = state_update[node_name]
                    
                    total_steps += 1
                    progress = min(total_steps * 10, 100)
                    progress_bar.progress(progress)
                    
                    with output_container:
                        if node_name == "researcher":
                            status_container.markdown("**RESEARCHER: Searching with Tavily**")
                            with st.expander("Research Findings", expanded=True):
                                st.text(current_state.get("research_findings", ""))
                        
                        elif node_name == "writing_team":
                            iteration = current_state.get("iteration", 1)
                            status_container.markdown(f"**WRITING TEAM: Creating script (Iteration {iteration})**")
                            with st.expander(f"Script Draft v{iteration}", expanded=True):
                                st.text(current_state.get("script", ""))
                        
                        elif node_name == "review_team":
                            iteration = current_state.get("iteration", 1)
                            rating = current_state.get("rating", 0)
                            feedback = current_state.get("feedback", "")
                            
                            status_container.markdown(f"**REVIEW TEAM: Rating script (Iteration {iteration})**")
                            
                            st.metric("Script Rating", f"{rating}/10")
                            
                            st.session_state.all_iterations.append({
                                "iteration": iteration,
                                "rating": rating,
                                "feedback": feedback,
                                "script": current_state.get("script", "")
                            })
                            
                            if rating >= 7:
                                st.success(f"APPROVED! Rating: {rating}/10")
                                progress_bar.progress(100)
                                
                                st.session_state.final_results = {
                                    "topic": current_state.get("topic"),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "research": current_state.get("research_findings", ""),
                                    "script": current_state.get("script", ""),
                                    "rating": rating,
                                    "feedback": feedback,
                                    "iterations": iteration,
                                    "all_iterations": st.session_state.all_iterations,
                                    "model_used": model_name
                                }
                                st.session_state.workflow_complete = True
                            else:
                                st.warning(f"Rating: {rating}/10 - NEEDS REVISION")
                                with st.expander("Feedback", expanded=True):
                                    st.info(feedback)
                                st.markdown("**Sending back to Writing Team for revision...**")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif start_btn and not topic:
        st.error("Please enter a topic")

with tab2:
    st.subheader("Production Results")
    
    if st.session_state.final_results:
        results = st.session_state.final_results
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Topic", results.get("topic", "N/A"))
        with col2:
            st.metric("Final Rating", f"{results.get('rating', 0)}/10")
        with col3:
            st.metric("Iterations", results.get("iterations", 0))
        with col4:
            st.metric("Model", results.get("model_used", "N/A"))
        
        st.divider()
        
        st.markdown("### Iteration History")
        for iter_data in results.get("all_iterations", []):
            with st.expander(f"Iteration {iter_data['iteration']} - Rating: {iter_data['rating']}/10"):
                st.markdown(f"**Rating:** {iter_data['rating']}/10")
                st.markdown(f"**Feedback:** {iter_data['feedback']}")
                st.markdown("**Script:**")
                st.text(iter_data['script'])
        
        st.divider()
        
        st.markdown("### Research Findings")
        st.text(results.get("research", ""))
        
        st.divider()
        
        st.markdown("### Final Approved Script")
        st.text(results.get("script", ""))
        
        st.divider()
        
        export_data = json.dumps(results, indent=2)
        st.download_button(
            label="Download Results (JSON)",
            data=export_data,
            file_name=f"production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    else:
        st.info("Complete a production to see results")

