import streamlit as st
import pandas as pd
from utils.search_engine import load_dataset, search_publications
from utils.ai_summarizer import summarize_text
from utils.graph_builder import build_graph
from dotenv import load_dotenv
import os, requests, io, json
from bs4 import BeautifulSoup

# Load .env
load_dotenv()

# 🌑 Page settings
st.set_page_config(page_title="BioOrbit", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    input, textarea, select {
        background-color: #2C2F36 !important;
        color: white !important;
        border-radius: 8px;
        border: 1px solid #444;
    }
    .stButton>button {
        background-color: #3A3F47;
        color: white;
        border-radius: 10px;
        border: 1px solid #666;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #6BE6C1;
        color: black;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(107, 230, 193, 0.3);
    }
    .link-button {
        display: inline-block;
        padding: 4px 10px;
        margin-left: 10px;
        background-color: #6BE6C1;
        color: black !important;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .link-button:hover {
        background-color: #4ad1a5;
        transform: translateY(-1px);
    }
    .result-card {
        background-color: #1E2128;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 4px solid #6BE6C1;
        transition: all 0.3s ease;
    }
    .result-card:hover {
        background-color: #252831;
        box-shadow: 0 4px 12px rgba(107, 230, 193, 0.2);
    }
    .stat-card {
        background: linear-gradient(135deg, #2C2F36 0%, #1E2128 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #444;
    }
    .stat-number {
        font-size: 2.5em;
        font-weight: bold;
        color: #6BE6C1;
    }
    .stat-label {
        font-size: 0.9em;
        color: #999;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2C2F36;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3A3F47;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧬 NASA Space Biology Explorer")
st.caption("Explore NASA's 608 space biology studies — online or offline!")

# Sidebar for settings
st.sidebar.header("⚙️ Settings")

# Load API key
default_api_key = os.getenv("GROQ_API_KEY", "")
api_key = st.sidebar.text_input("Groq API Key (leave blank for offline mode):", value=default_api_key, type="password")

# Add filter options in sidebar
st.sidebar.header("🔍 Filters")
year_filter = st.sidebar.checkbox("Filter by Year Range", value=False)
if year_filter:
    year_min = st.sidebar.number_input("From Year", min_value=1950, max_value=2025, value=2000)
    year_max = st.sidebar.number_input("To Year", min_value=1950, max_value=2025, value=2025)

# Display mode
display_mode = st.sidebar.radio("Display Mode", ["Compact", "Detailed"], index=0)

# Visualization mode
st.sidebar.header("📊 Visualization Options")
viz_mode = st.sidebar.radio("Graph Type", ["Interactive Network", "Plotly Charts", "Both"], index=2)

# Local cache file for summaries
CACHE_FILE = "summary_cache.json"

# Load existing cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}


# Load dataset
@st.cache_data
def load_data():
    return load_dataset("nasa_space_biology_608.csv")


df = load_data()

# Display stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(df)}</div>
        <div class="stat-label">Total Studies</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    unique_authors = df['authors'].nunique() if 'authors' in df.columns else "N/A"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{unique_authors}</div>
        <div class="stat-label">Authors</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    unique_years = df['year'].nunique() if 'year' in df.columns else "N/A"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{unique_years}</div>
        <div class="stat-label">Years Covered</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{"✓" if api_key else "✗"}</div>
        <div class="stat-label">AI Mode</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Search input with suggestions
query = st.text_input("🔎 Search Topic (e.g., microgravity, plants, stem cells)", placeholder="Enter a keyword...")

# Add example queries
with st.expander("💡 Example Searches"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌱 Plant Biology"):
            query = "plant"
    with col2:
        if st.button("🧫 Microgravity"):
            query = "microgravity"
    with col3:
        if st.button("🧬 Stem Cells"):
            query = "stem cells"

if query:
    try:
        with st.spinner("Searching publications..."):
            results = search_publications(query, df)

            # Apply filters
            if year_filter and 'year' in results.columns:
                results = results[(results['year'] >= year_min) & (results['year'] <= year_max)]

        if results.empty:
            st.warning("No results found. Try another keyword or adjust filters.")
        else:
            st.success(f"Found {len(results)} result(s) for '{query}'")

            # Add export button
            col1, col2 = st.columns([6, 1])
            with col2:
                csv = results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export",
                    data=csv,
                    file_name=f"nasa_biology_{query}.csv",
                    mime="text/csv",
                )

            st.subheader(f"📚 Results for '{query}'")

            # Display results
            for i, row in enumerate(results.itertuples(), start=1):
                title = row.title
                link = getattr(row, "link", None)
                abstract = getattr(row, "abstract", "")[:200] + "..." if hasattr(row, "abstract") else ""
                year = getattr(row, "year", "N/A")
                authors = getattr(row, "authors", "Unknown")

                with st.container():
                    if display_mode == "Detailed":
                        st.markdown(f"""
                        <div class="result-card">
                            <h4>{i}. {title}</h4>
                            <p style="color: #999; font-size: 0.9em;">
                                <strong>Year:</strong> {year} | <strong>Authors:</strong> {authors if len(str(authors)) < 50 else str(authors)[:50] + '...'}
                            </p>
                            <p style="color: #ccc; font-size: 0.95em;">{abstract}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        if link:
                            st.markdown(f"<a href='{link}' target='_blank' class='link-button'>🔗 View Publication</a>",
                                        unsafe_allow_html=True)
                    else:
                        if link:
                            st.markdown(
                                f"""<div class="result-card">
                                <strong>{i}. {title}</strong> ({year}) 
                                <a href='{link}' target='_blank' class='link-button'>🔗 Link</a>
                                </div>""",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f"""<div class="result-card"><strong>{i}. {title}</strong> ({year})</div>""",
                                        unsafe_allow_html=True)

            # AI Summary Section
            # Replace the AI Summary Section in your app.py with this fixed version:

            # AI Summary Section
            if api_key:
                st.markdown("---")
                if st.button("✨ Generate AI Summary of Results"):
                    with st.spinner("Generating summary..."):
                        try:
                            # Check if abstract column exists
                            if 'abstract' in results.columns and not results['abstract'].dropna().empty:
                                # Use abstracts if available
                                summary_text = " ".join(results['abstract'].dropna().head(5).tolist())
                            elif 'description' in results.columns and not results['description'].dropna().empty:
                                # Try description column as fallback
                                summary_text = " ".join(results['description'].dropna().head(5).tolist())
                            else:
                                # Use titles and any available text
                                summary_text = f"Research papers about {query}: " + ". ".join(
                                    results['title'].head(10).tolist())

                            # Check if we have enough text
                            if len(summary_text.strip()) < 50:
                                st.warning(
                                    "Not enough text content available for summarization. Try including abstracts in your dataset.")
                            else:
                                summary = summarize_text(summary_text, api_key)
                                st.success("Summary Generated!")
                                st.markdown(f"""
                                <div style="background-color: #1E2128; padding: 20px; border-radius: 10px; border-left: 4px solid #6BE6C1;">
                                    <h4 style="color: #6BE6C1; margin-top: 0;">📝 AI Summary</h4>
                                    <p style="color: #CCC; line-height: 1.6;">{summary}</p>
                                </div>
                                """, unsafe_allow_html=True)

                        except KeyError as ke:
                            st.error(f"❌ Column not found: {ke}")
                            st.info(
                                "💡 Your dataset might be missing the 'abstract' column. The summary feature requires paper abstracts or descriptions.")
                        except Exception as e:
                            st.error(f"❌ Failed to generate summary: {e}")
                            st.info(
                                "💡 Make sure your Groq API key is valid and you have an active internet connection.")

            # ============ VISUALIZATIONS ============
            st.markdown("---")
            st.subheader("📊 Research Visualizations")

            # Option 1: Interactive Network Graph (PyVis)
            if viz_mode in ["Interactive Network", "Both"]:
                st.markdown("### 🕸️ Interactive Knowledge Graph")
                with st.spinner("Building interactive network graph..."):
                    try:
                        graph_path = build_graph(df, query)
                        with open(graph_path, "r", encoding="utf-8") as f:
                            html_code = f.read()
                        st.components.v1.html(html_code, height=650, scrolling=True)
                    except Exception as e:
                        st.error(f"⚠️ Could not build interactive graph: {e}")
                        st.exception(e)

            # Option 2: Plotly Charts
            if viz_mode in ["Plotly Charts", "Both"]:
                try:
                    from utils.visualizations import (
                        generate_topic_network,
                        generate_citation_impact_scatter,
                        generate_timeline_visualization
                    )

                    st.markdown("### 📈 Statistical Analysis")

                    tab1, tab2, tab3 = st.tabs(["🔗 Network Graph", "💫 Impact Analysis", "📅 Timeline"])

                    with tab1:
                        with st.spinner("Building author-paper network..."):
                            try:
                                fig = generate_topic_network(df, query, results)
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"⚠️ Could not build network: {e}")

                    with tab2:
                        with st.spinner("Analyzing research impact..."):
                            try:
                                fig = generate_citation_impact_scatter(df, query, results)
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"⚠️ Could not build impact analysis: {e}")

                    with tab3:
                        with st.spinner("Creating publication timeline..."):
                            try:
                                fig = generate_timeline_visualization(df, query, results)
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"⚠️ Could not build timeline: {e}")

                except ImportError:
                    st.error("⚠️ Visualization module not found. Make sure utils/visualizations.py exists.")
                except Exception as e:
                    st.error(f"⚠️ Visualization error: {e}")
                    st.exception(e)

    except Exception as e:
        st.error(f"⚠️ Search error: {e}")
        st.exception(e)

else:
    st.info("👆 Enter a topic above to explore NASA's biology studies.")

    # Show recent or popular topics when no query
    st.subheader("🌟 Getting Started")
    st.markdown("""
    This tool helps you explore NASA's comprehensive space biology research database. Features include:

    - 🔍 **Smart Search**: Find relevant studies using keywords
    - 📊 **Visual Networks**: See connections between related papers
    - 🤖 **AI Summaries**: Get quick insights (requires API key)
    - 📥 **Export Data**: Download results for further analysis
    - 🎯 **Filters**: Narrow down by year and other criteria

    Try searching for topics like: **microgravity**, **radiation**, **plant biology**, **immune system**, or **bone loss**
    """)

# Footer
st.markdown("---")
st.caption("Built with ❤️ for space biology research | Data: NASA Space Biology Database")