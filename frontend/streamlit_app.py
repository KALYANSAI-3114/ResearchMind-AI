"""
Streamlit Frontend
Interactive UI for ResearchMind AI
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="ResearchMind AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# API base URL (can be configured)
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# Page title
st.title("📚 ResearchMind AI")
st.markdown("### Agentic RAG Research Paper Assistant")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a feature:",
        ["Home", "Upload Paper", "Search Papers", "Summarize", "Compare Papers"]
    )
    
    st.divider()
    st.markdown("### About")
    st.markdown("""
    **ResearchMind AI** helps researchers:
    - 📄 Upload & analyze papers
    - 🔍 Find related research
    - 📊 Compare methodologies
    - 📋 Generate summaries
    - 🔎 Identify research gaps
    """)
    
    st.divider()
    st.markdown("### API Status")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✓ Backend Connected")
        else:
            st.error("✗ Backend Error")
    except:
        st.error("✗ Backend Offline")


# Home Page
if page == "Home":
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## Welcome to ResearchMind AI 🤖
        
        An intelligent research assistant that automates literature analysis using:
        
        - **Agentic AI**: Multi-agent reasoning for complex tasks
        - **RAG**: Retrieval-Augmented Generation for accurate answers
        - **Vector Embeddings**: Semantic search across papers
        - **External APIs**: arXiv & Semantic Scholar integration
        
        ### Quick Start
        1. Upload a research paper (PDF)
        2. Get an instant summary
        3. Find related papers
        4. Compare with existing research
        5. Identify research gaps
        """)
    
    with col2:
        st.markdown("""
        ### Key Features
        
        ✅ **PDF Upload & Parsing**
        - Automatic text extraction
        - Metadata detection
        
        ✅ **AI Summarization**
        - Objective extraction
        - Methodology overview
        - Key findings
        
        ✅ **Paper Retrieval**
        - arXiv search
        - Semantic Scholar search
        - Keyword extraction
        
        ✅ **Smart Comparison**
        - Methodology comparison
        - Strengths/weaknesses analysis
        - Gap identification
        """)


# Upload Paper Page
elif page == "Upload Paper":
    st.header("📄 Upload & Analyze Research Paper")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**File:** {uploaded_file.name}")
            st.info(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        
        if st.button("Process Paper", use_container_width=True):
            with st.spinner("Processing paper..."):
                try:
                    # Prepare file for upload
                    files = {"file": uploaded_file}
                    response = requests.post(
                        f"{API_BASE_URL}/upload-paper",
                        files=files,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✓ Paper uploaded successfully!")
                        
                        # Store doc_id in session
                        st.session_state.uploaded_doc_id = result.get("doc_id")
                        
                        with st.expander("View Details", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Title", result.get("title", "N/A")[:30])
                            col2.metric("Pages", result.get("pages", "N/A"))
                            col3.metric("Text Length", f"{result.get('text_length', 0) // 1000}K chars")
                        
                        st.balloons()
                    else:
                        st.error(f"Upload failed: {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Q&A Section
    if hasattr(st.session_state, "uploaded_doc_id") and st.session_state.uploaded_doc_id:
        st.divider()
        st.subheader("❓ Ask Questions About This Paper")
        
        question = st.text_input(
            "Ask a question about the paper",
            placeholder="e.g., 'What is the main contribution?', 'What methods were used?'",
            key="question_input"
        )
        
        if question and st.button("Get Answer", use_container_width=True):
            with st.spinner("Searching paper for answer..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/ask-question",
                        params={
                            "doc_id": st.session_state.uploaded_doc_id,
                            "question": question
                        },
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "success":
                            st.success("✓ Answer found!")
                            
                            with st.expander("📌 Q&A Result", expanded=True):
                                st.markdown("**Question:**")
                                st.write(f"_{question}_")
                                
                                st.markdown("**Answer from Paper:**")
                                st.write(result.get("answer", "No answer found"))

                                if result.get("is_generative"):
                                    provider = result.get("generation_provider", "LLM")
                                    model = result.get("generation_model", "unknown model")
                                    st.caption(f"Generated with {provider}: {model}")
                                else:
                                    st.warning("LLM generation was not available; showing best synthesized fallback from retrieved context.")

                                if result.get("retrieved_chunk_previews"):
                                    with st.expander("Retrieved chunks", expanded=False):
                                        if result.get("search_query"):
                                            st.caption(f"Search query: {result['search_query']}")
                                        for chunk in result["retrieved_chunk_previews"]:
                                            st.markdown(
                                                f"**Chunk {chunk['chunk_index']}** "
                                                f"score={chunk['score']} "
                                                f"keyword={chunk['keyword_score']} "
                                                f"distance={chunk['distance']}"
                                            )
                                            st.write(chunk["preview"])
                        else:
                            st.warning(result.get("message", "Could not find relevant information"))
                    else:
                        st.error(f"Error: {response.text}")
                
                except Exception as e:
                    st.error(f"Error asking question: {str(e)}")
        
        st.info("💡 Tip: Ask specific questions about methodology, results, limitations, or any other aspect of the paper")
    
    elif not uploaded_file:
        st.info("👆 Upload a PDF to get started with analysis and Q&A")


# Search Papers Page
elif page == "Search Papers":
    st.header("🔍 Search Related Papers")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Enter search query", placeholder="e.g., 'agentic RAG', 'neural networks'")
    
    with col2:
        max_results = st.slider("Max results per source", 3, 10, 5)
    
    if search_query and st.button("Search", use_container_width=True):
        with st.spinner("Searching papers..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/search-related",
                    params={"query": search_query, "max_results": max_results},
                    timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # View results
                    if results["total_results"] > 0:
                        st.success(f"✓ Found {results['total_results']} papers")
                    else:
                        st.warning(f"⚠️ {results.get('message', 'No results found')}")
                    
                    # arXiv results
                    if results["arxiv_papers"]:
                        st.subheader(f"📌 arXiv Papers ({len(results['arxiv_papers'])})")
                        for i, paper in enumerate(results["arxiv_papers"], 1):
                            with st.expander(f"{i}. {paper.get('title', 'Unknown')[:80]}"):
                                st.markdown(f"**Authors:** {', '.join(paper.get('authors', [])[:3])}")
                                st.markdown(f"**arXiv ID:** {paper.get('arxiv_id', 'N/A')}")
                                st.markdown(f"**Published:** {paper.get('published', 'N/A')}")
                                st.markdown(f"**Summary:** {paper.get('summary', '')[:300]}...")
                                if paper.get('url'):
                                    st.markdown(f"[View on arXiv]({paper['url']})")
                    else:
                        st.info("📌 arXiv - Currently rate-limited or unavailable")
                    
                    # Semantic Scholar results
                    if results["semantic_scholar_papers"]:
                        st.subheader(f"🎓 Semantic Scholar Papers ({len(results['semantic_scholar_papers'])})")
                        for i, paper in enumerate(results["semantic_scholar_papers"], 1):
                            with st.expander(f"{i}. {paper.get('title', 'Unknown')[:80]}"):
                                st.markdown(f"**Authors:** {', '.join(paper.get('authors', [])[:3])}")
                                st.markdown(f"**Year:** {paper.get('year', 'N/A')}")
                                st.markdown(f"**Citations:** {paper.get('citation_count', 0)}")
                                if paper.get('abstract'):
                                    st.markdown(f"**Abstract:** {paper['abstract'][:300]}...")
                                if paper.get('url'):
                                    st.markdown(f"[View Paper]({paper['url']})")
                    else:
                        st.info("🎓 Semantic Scholar - Currently rate-limited or unavailable")
                
                else:
                    st.error(f"Search failed: {response.text}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


# Summarize Page
elif page == "Summarize":
    st.header("📋 Paper Summarization")
    
    summary_option = st.radio("Choose input method:", ["Use uploaded paper", "Enter text directly"])
    
    if summary_option == "Use uploaded paper":
        if "uploaded_doc_id" in st.session_state:
            if st.button("Generate Summary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/summarize",
                            params={"doc_id": st.session_state.uploaded_doc_id},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            summary = result["summary"]
                            
                            st.success("✓ Summary generated!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("Objective")
                                st.write(summary.get("objective", "N/A"))
                                
                                st.subheader("Methodology")
                                st.write(summary.get("methodology", "N/A"))
                            
                            with col2:
                                st.subheader("Results")
                                st.write(summary.get("results", "N/A"))
                                
                                st.subheader("Limitations")
                                st.write(summary.get("limitations", "N/A"))
                            
                            st.subheader("Key Contributions")
                            st.write(summary.get("key_contributions", "N/A"))
                        
                        else:
                            st.error(f"Summarization failed: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.warning("Please upload a paper first on the 'Upload Paper' page")
    
    else:
        paper_text = st.text_area("Paste paper text or abstract", height=200)
        
        if paper_text and st.button("Generate Summary", use_container_width=True):
            with st.spinner("Generating summary..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/summarize",
                        params={"paper_text": paper_text},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        summary = result["summary"]
                        
                        st.success("✓ Summary generated!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Objective")
                            st.write(summary.get("objective", "N/A"))
                            
                            st.subheader("Methodology")
                            st.write(summary.get("methodology", "N/A"))
                        
                        with col2:
                            st.subheader("Results")
                            st.write(summary.get("results", "N/A"))
                            
                            st.subheader("Limitations")
                            st.write(summary.get("limitations", "N/A"))
                    
                    else:
                        st.error(f"Summarization failed: {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# Compare Papers Page
elif page == "Compare Papers":
    st.header("📊 Compare Research Papers")
    
    query = st.text_input("Enter topic to find and compare papers", placeholder="e.g., 'large language models'")
    
    if query and st.button("Search & Compare", use_container_width=True):
        with st.spinner("Searching and comparing papers..."):
            try:
                # First search for papers
                search_response = requests.post(
                    f"{API_BASE_URL}/search-related",
                    params={"query": query, "max_results": 5},
                    timeout=60
                )
                
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    
                    if search_results.get("total_results", 0) > 0:
                        st.success(f"✓ Found {search_results['total_results']} papers")
                    else:
                        st.warning(search_results.get("message", "No papers found"))
                    
                    # Prepare papers for comparison
                    papers_for_comparison = {
                        "main_paper_id": None,
                        "related_paper_ids": None,
                        "query": query
                    }
                    
                    # Call comparison endpoint
                    compare_response = requests.post(
                        f"{API_BASE_URL}/compare-papers",
                        params=papers_for_comparison,
                        timeout=60
                    )
                    
                    if compare_response.status_code == 200:
                        comparison_result = compare_response.json()
                        
                        if comparison_result.get("status") == "success":
                            comparison = comparison_result.get("comparison", {})
                            
                            st.success("✓ Comparison completed!")
                            
                            # Display comparison
                            st.subheader("Comparison Results")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### Methodologies")
                                for method in comparison.get("methodologies", []):
                                    st.write(f"**{method.get('paper', 'Unknown')}**")
                                    st.write(method.get("methodology", "N/A")[:200])
                                    st.divider()
                                
                                if not comparison.get("methodologies"):
                                    st.info("Methodology details available in paper analysis")
                            
                            with col2:
                                st.markdown("### Insights")
                                for insight in comparison.get("insights", []):
                                    st.write(f"• {insight}")
                                
                                if not comparison.get("insights"):
                                    st.info("Analysis: Paper is available for detailed study")
                            
                            if comparison.get("similarities"):
                                st.subheader("Similarities")
                                for sim in comparison.get("similarities", []):
                                    st.write(f"**{sim.get('paper', 'Unknown')}**")
                                    st.write(f"Common topics: {', '.join(sim.get('common_topics', []))}")
                            
                            if comparison.get("differences"):
                                st.subheader("Differences")
                                for diff in comparison.get("differences", []):
                                    st.write(f"**{diff.get('paper', 'Unknown')}**")
                                    st.write(f"Unique aspects: {', '.join(diff.get('unique_aspects', []))}")
                            
                            # Show status if partial
                            if comparison.get("analysis_type") == "single_paper":
                                st.info("ℹ️ Showing paper analysis (external APIs unavailable)")
                                st.markdown("Try searching again later for full comparisons with related papers")
                        
                        else:
                            st.warning(comparison_result.get("message", "Comparison not available"))
                    
                    else:
                        st.error(f"Comparison failed: {compare_response.text}")
                
                else:
                    st.error(f"Search failed: {search_response.text}")
            
            except requests.exceptions.Timeout:
                st.error("Request timed out. APIs might be slow. Try again in a moment.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🚀 ResearchMind AI v1.0")
with col2:
    st.caption("Powered by LangGraph + FastAPI")
with col3:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
