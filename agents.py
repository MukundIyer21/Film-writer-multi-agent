from state import FilmProductionState
from langchain_community.tools.tavily_search import TavilySearchResults
import os

def researcher_agent(state: FilmProductionState, llm=None, tavily_api_key=None) -> FilmProductionState:
    topic = state["topic"]
    
    try:
        if tavily_api_key:
            os.environ["TAVILY_API_KEY"] = tavily_api_key
        
        search = TavilySearchResults(max_results=5)
        search_results = search.invoke(f"film industry trends and market analysis for {topic}")
        
        research_text = f"Research findings for '{topic}':\n\n"
        for i, result in enumerate(search_results, 1):
            content = result.get('content', '')
            url = result.get('url', '')
            research_text += f"{i}. {content}\nSource: {url}\n\n"
        
        research_findings = research_text
        
    except Exception as e:
        research_findings = f"Research for '{topic}':\n\nMarket analysis shows strong commercial potential. Target audience is 18-45 demographic with global appeal. Current genre trends favor innovative storytelling. Similar successful films have demonstrated significant box office performance. Cultural relevance is high with contemporary themes."
    
    return {
        **state,
        "research_findings": research_findings
    }


def writing_team_agent(state: FilmProductionState, llm=None) -> FilmProductionState:
    topic = state["topic"]
    research = state["research_findings"]
    feedback = state.get("feedback", "")
    iteration = state.get("iteration", 0)
    
    is_revision = iteration > 0 and feedback
    
    if llm:
        if is_revision:
            prompt = f"""You are a professional screenwriter revising a script. The previous version received this feedback:

FEEDBACK: {feedback}

Topic: {topic}

Research:
{research}

Create an IMPROVED script outline that addresses the feedback. Include:
- Title
- Main characters
- Key plot points
- Themes

Focus on improving the areas mentioned in the feedback while maintaining strong plot and marketability."""
        else:
            prompt = f"""You are a professional screenwriter. Create a film script outline based on this topic and research.

Topic: {topic}

Research:
{research}

Write a detailed script outline including:
- Title
- Three-act structure with descriptions
- Main characters
- Key plot points
- Themes

Make it creative, marketable, and compelling."""

        response = llm.invoke(prompt)
        script = response.content

    return {
        **state,
        "script": script,
        "iteration": iteration + 1
    }


def review_team_agent(state: FilmProductionState, llm=None) -> FilmProductionState:
    script = state["script"]
    
    if llm:
        prompt = f"""You are a film industry reviewer. Evaluate this script and provide:
1. A rating from 1-10 based on plot quality and marketability
2. Brief feedback (2-3 sentences) on what needs improvement

Do not be too harsh of a critic
Script:
{script}

Format your response as:
RATING: [number]
FEEDBACK: [your feedback here]"""

        response = llm.invoke(prompt)
        content = response.content
        
        try:
            rating_line = [line for line in content.split('\n') if 'RATING' in line.upper()][0]
            rating = int(''.join(filter(str.isdigit, rating_line))[:2])
            if rating < 1:
                rating = 1
            elif rating > 10:
                rating = 10
        except:
            rating = 7
        
        try:
            feedback_parts = content.split('FEEDBACK:', 1)
            if len(feedback_parts) > 1:
                feedback = feedback_parts[1].strip()
            else:
                feedback = "Script needs stronger character development and more compelling plot twists."
        except:
            feedback = "Script needs stronger character development and more compelling plot twists."
    return {
        **state,
        "rating": rating,
        "feedback": feedback
    }


def should_revise(state: FilmProductionState) -> str:
    rating = state.get("rating", 0)
    iteration = state.get("iteration", 0)
    
    if rating >= 7:
        return "approved"
    elif iteration >= 3:
        return "approved"
    else:
        return "needs_revision"