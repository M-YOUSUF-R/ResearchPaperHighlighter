import streamlit as st
import fitz  # PyMuPDF
import re
import io
import os

# Set Page Config
st.set_page_config(page_title="ReviewHighlighter Web", layout="wide")

def process_pdf(pdf_file, keywords):
    """Extracts text and finds sentences matching keywords."""
    # Open PDF from the uploaded file buffer
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    
    full_text = ""
    for page in doc:
        full_text += page.get_text() + " "
    
    clean_text = full_text.replace('\n', ' ').replace('  ', ' ')
    sentences = re.split('(?<=[.?!])\\s+', clean_text)
    
    # Initialize data structure
    extracted_data = {kw: {'count': 0, 'sentences': set()} for kw in keywords}
    
    # Find matching sentences
    for sentence in sentences:
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', sentence, re.IGNORECASE):
                extracted_data[keyword]['sentences'].add(sentence.strip())

    # Count total occurrences
    for keyword in keywords:
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', clean_text, re.IGNORECASE))
        extracted_data[keyword]['count'] = count
    
    return doc, extracted_data

def generate_highlighted_pdf(doc, selected_keywords):
    """Adds highlights to the PDF and returns it as a byte stream."""
    keywords_lower = {k.lower() for k in selected_keywords}
    total_highlights = 0
    
    for page in doc:
        words = page.get_text('words') # w[4] is the text content
        for w in words:
            if w[4].lower() in keywords_lower:
                rect = fitz.Rect(w[:4])
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=(1, 1, 0)) # Yellow
                highlight.update()
                total_highlights += 1
                
    # Save to a memory buffer instead of a local file
    output_buffer = io.BytesIO()
    doc.save(output_buffer, garbage=4, deflate=True, clean=True)
    doc.close()
    return output_buffer.getvalue(), total_highlights

# --- UI Layout ---
st.title("📄 ReviewHighlighter")
st.markdown("Extract sentences and highlight research papers automatically.")
footer = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: white;
    color: black;
    text-align: center;
    padding: 10px;
}
</style>
<div class="footer">
    <p>Developed by <a href="https://carsit.bcet.uk" target="_blank">CARSIT</a> & Customized by <a href="https://github.com/M-YOUSUF-R" target="_blank">Md Yousuf</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)


# 1. Inputs
with st.sidebar:
    st.header("1. Settings")
    uploaded_file = st.file_uploader("Upload PDF File", type="pdf")
    
    # Pre-filled keywords from your original source code 
    default_keywords = 'Problem, Problems, verify, verifies, verified, verification, discover, discovers, discovered, discovery, discoveries, error, errors, mistakes, finding, findings, contradict, methodology, methodologies, outcome, outcomes, contradicts, contradicted, contradictory, justify, justifies, justified, justification, propose, proposes, proposed, challenge, challenges, evident, evidence, results, validate, validates, validated, validation, erroneous, deficit, deficits, performance, performs, performed, outperforms, outperformed, evaluation, argument, arguments, argues, argued, suggest, suggests, suggested, highlight, highlights, highlighted, limitation, limitations, gap, gaps, novel, novelty, algorithm, algorithms, framework, frameworks, model, models, implement, implements, implemented, implementation, application, applications, implication, implications, hypothesis, hypotheses, confirmation, clarifies, clarification, argumentative, complexity, complexities, discrepancy, discrepancies, contrast, sharp contrast, challenging, anomaly, anomalies, pragmatic, heuristic, contribute, contributes, contributed, contribution, contributions, report, reports, reported, aim, aims, goals, qualitative, quantitative, KPI, insight, insights, primary, primary data, Data Collection, survey, surveys, interview, interviews, simulation, simulation experiment, performance evaluation, observation, observations, experiment, experiments'
    
    keywords_input = st.text_area("Keywords (CSV)", value=default_keywords, height=300)
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]

# 2. Processing
if uploaded_file and st.sidebar.button("2. Process PDF"):
    with st.spinner("Analyzing PDF..."):
        # Reset file pointer for re-reading
        uploaded_file.seek(0)
        doc, results = process_pdf(uploaded_file, keywords)
        
        # Save results to session state for the next step
        st.session_state['doc'] = doc
        st.session_state['results'] = results
        st.session_state['processed'] = True

# 3. Display Results
if 'processed' in st.session_state:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Extracted Sentences Preview")
        for kw, data in st.session_state['results'].items():
            if data['sentences']:
                with st.expander(f"Keyword: {kw.upper()} ({len(data['sentences'])} sentences)"):
                    for i, sentence in enumerate(sorted(list(data['sentences'])), 1):
                        st.write(f"**{i}.** {sentence}")

    with col2:
        st.subheader("📊 Keyword Counts")
        found_keywords = [kw for kw, data in st.session_state['results'].items() if data['count'] > 0]
        if found_keywords:
            for kw in found_keywords:
                st.write(f"**{kw}:** {st.session_state['results'][kw]['count']}")
            
            st.divider()
            st.subheader("3. Export")
            
            # Selection for highlighting
            to_highlight = st.multiselect(
                "Select keywords to highlight in PDF:", 
                options=found_keywords,
                default=found_keywords
            )
            
            if st.button("Generate Highlighted PDF"):
                pdf_bytes, count = generate_highlighted_pdf(st.session_state['doc'], to_highlight)
                st.success(f"Added {count} highlights!")
                
                st.download_button(
                    label="Download Highlighted PDF",
                    data=pdf_bytes,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_highlighted.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("No keywords found in the document.")
else:
    st.info("Upload a PDF and click 'Process PDF' in the sidebar to start.")
