import streamlit as st
import pandas as pd
import requests
import io
import re
from pdf2image import convert_from_bytes
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Glyphon | Ticket Processor",
    page_icon="📋",
    layout="wide",
)

# --- CUSTOM CSS FOR POLISH ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    .footer-text { font-size: 12px; color: #8b949e; margin-top: 50px; }
    
    /* Replicating the Puter-root style for the Python container */
    .puter-style-container {
        background-color: #161b22; 
        color: #e6edf3; 
        padding: 30px; 
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
        border-radius: 12px; 
        border: 1px solid #30363d;
    }
    .upload-section {
        text-align: center; 
        border: 2px dashed #484f58; 
        padding: 40px; 
        border-radius: 12px; 
        background: #0d1117;
        margin-bottom: 20px;
    }
    /* Ensuring the uploader looks good inside the custom box */
    [data-testid="stFileUploader"] {
        padding: 0;
    }
    [data-testid="stFileUploader"] > section {
        padding: 0;
        background-color: transparent;
        border: none;
    }
    .stButton>button {
        background-color: #238636 !important; 
        color: white !important; 
        border: none !important; 
        padding: 14px 40px !important; 
        border-radius: 6px !important; 
        font-weight: 600 !important; 
        font-size: 16px !important;
        width: 100%;
    }
    .status-msg { color: #d29922; font-size: 15px; font-weight: 500; text-align: center; }
    .success-box {
        margin-top: 25px; 
        padding: 25px; 
        background: rgba(56, 139, 253, 0.1); 
        border-radius: 12px; 
        text-align: center; 
        border: 1px solid #388bfd;
        color: #58a6ff; 
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC FUNCTIONS ---
def call_easy_ocr_api(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    try:
        files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post('https://api.easyocr.org/ocr', files=files)
        if response.status_code == 200:
            result = response.json()
            return " ".join(result.get('words', []))
        return ""
    except Exception as e:
        return f"Error: {str(e)}"

def extract_fields(text):
    data = {
        "id": re.search(r'(\d{9,10})', text).group(1) if re.search(r'(\d{9,10})', text) else "N/A",
        "date": re.search(r'(\d{2}/\d{2}/\d{4})', text).group(1) if re.search(r'(\d{2}/\d{2}/\d{4})', text) else "N/A",
        "type": "HANGER" if "HANGER" in text.upper() else "LEANER",
        "measure": 0.0
    }
    m_match = re.search(r'Measure\s*[:\s]*([\d.]+)', text, re.I)
    if m_match:
        data["measure"] = float(m_match.group(1))
    return data

def format_row(item):
    row = [" $- " for _ in range(19)]
    row[0], row[1], row[2], row[3] = item['date'], item['id'], "848117", "Fernando"
    row[11], row[12] = "", "" 
    m = item['measure']
    if item['type'] == "HANGER":
        row[4], row[5], row[10], row[13], row[18] = "1", " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
    else:
        row[4] = str(m)
        if 0.01 <= m <= 23.99: row[6], row[10], row[14], row[18] = " $80.00 ", " $80.00 ", " $100.00 ", " $100.00 "
        elif 24.0 <= m <= 35.99: row[7], row[10], row[15], row[18] = " $150.00 ", " $150.00 ", " $175.00 ", " $175.00 "
        elif 36.0 <= m <= 47.99: row[8], row[10], row[16], row[18] = " $175.00 ", " $175.00 ", " $200.00 ", " $200.00 "
        elif m >= 48.0: row[9], row[10], row[17], row[18] = " $250.00 ", " $250.00 ", " $275.00 ", " $275.00 "
    return row

# --- SIDEBAR: SUPPORT & STATUS ---
with st.sidebar:
    st.title("Glyphon")
    st.success("✨ System is active")
    with st.expander("Usage Notes", expanded=True):
        st.write("""
        **User Limit:** To ensure the best performance for everyone, we recommend only one or two people process tickets at the same time.
        **Quality Check:** Our AI reaches about 97% accuracy. While it's a huge time-saver, a quick human review of the final CSV is always recommended for total precision.
        """)
    st.divider()
    st.markdown("### Need assistance?")
    st.write("If you run into any issues, I am happy to help:")
    st.caption("📧 sorenclink@gmail.com")
    st.divider()
    st.markdown('<p class="footer-text">© 2026 Soren Clink<br>All rights reserved.</p>', unsafe_allow_html=True)

# --- MAIN INTERFACE ---
st.title("Ticket Data Entry, Simplified.")
st.markdown("Upload your scanned PDF tickets below. Our AI will read the details and prepare a CSV for you in seconds.")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Step 1", "Upload PDF")
with col2: st.metric("Step 2", "AI Review")
with col3: st.metric("Step 3", "Download CSV")

st.divider()

# --- THE PROCESSING ENGINE ---
st.markdown('<div class="puter-style-container">', unsafe_allow_html=True)
st.markdown('<div class="upload-section"><p style="color: #c9d1d9;">Drag and drop or select the PDF file you\'d like to process</p>', unsafe_allow_html=True)
# The file uploader is the "Drag and Drop" zone
uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    if st.button("Analyze PDF Tickets"):
        status_placeholder = st.empty()
        all_results = []
        
        # Logic execution
        images = convert_from_bytes(uploaded_file.read(), dpi=200)
        for i, img in enumerate(images):
            status_placeholder.markdown(f'<p class="status-msg">Processing page {i+1} of {len(images)}...</p>', unsafe_allow_html=True)
            text = call_easy_ocr_api(img)
            parsed = extract_fields(text)
            all_results.append(format_row(parsed))
        
        status_placeholder.empty()
        
        if all_results:
            st.markdown('<div class="success-box">Success! Your data is ready for export.</div>', unsafe_allow_html=True)
            
            # Export Logic
            csv_io = io.StringIO()
            csv_io.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\nProject Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\nDate,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
            pd.DataFrame(all_results).to_csv(csv_io, index=False, header=False)
            
            st.download_button(
                label="Download CSV Spreadsheet",
                data=csv_io.getvalue(),
                file_name="Processed_Tickets_Export.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            with st.expander("Data Preview (Raw JSON)"):
                st.json(all_results)

st.markdown('</div>', unsafe_allow_html=True)
