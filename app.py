import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
from gradio_client import Client, handle_file
import io
import re
import os

# --- PRODUCTION CONFIG ---
# Update this with your actual HF Space URL
HF_SPACE_URL = "https://your-username-your-space.hf.space/" 

st.set_page_config(page_title="Ticket Master Pro", layout="wide")

def get_ai_data(img_pil):
    try:
        client = Client(HF_SPACE_URL)
        # Save temp image for the AI to read
        img_path = "temp_page.png"
        img_pil.save(img_path)
        
        result = client.predict(
            image=handle_file(img_path),
            api_name="/predict"
        )
        return str(result)
    except Exception as e:
        return f"ERROR: {str(e)}"

def extract_logic(text):
    # Specialized Regex for the "Unit Rate Ticket" format
    data = {
        "id": re.search(r'(\d{9})', text).group(1) if re.search(r'(\d{9})', text) else "N/A",
        "date": re.search(r'(\d{2}/\d{2}/\d{4})', text).group(1) if re.search(r'(\d{2}/\d{2}/\d{4})', text) else "N/A",
        "type": "HANGER" if "HANGER" in text.upper() else "LEANER"
    }
    
    # Look for the Measure (Handwritten decimal)
    m_match = re.search(r'Measure\s*[:\s]*([\d.]+)', text, re.I)
    data["measure"] = float(m_match.group(1)) if m_match else 0.0
    return data

def build_row(item):
    # The Exact 19-Column Master Log Structure
    row = [" $- " for _ in range(19)]
    row[0], row[1], row[2], row[3] = item['date'], item['id'], "848117", "Fernando"
    row[11], row[12] = "", "" # Gaps
    
    m = item['measure']
    if item['type'] == "HANGER":
        row[4], row[5], row[10], row[13], row[18] = "1", " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
    else:
        row[4] = str(m)
        if 0.01 <= m <= 23.99:
            row[6], row[10], row[14], row[18] = " $80.00 ", " $80.00 ", " $100.00 ", " $100.00 "
        elif 24.0 <= m <= 35.99:
            row[7], row[10], row[15], row[18] = " $150.00 ", " $150.00 ", " $175.00 ", " $175.00 "
        elif 36.0 <= m <= 47.99:
            row[8], row[10], row[16], row[18] = " $175.00 ", " $175.00 ", " $200.00 ", " $200.00 "
        elif m >= 48.0:
            row[9], row[10], row[17], row[18] = " $250.00 ", " $250.00 ", " $275.00 ", " $275.00 "
    return row

# --- APP UI ---
st.title("🌲 Master Log Production AI")
st.info("Using Microsoft Florence-2 Transformer for high-accuracy ticket parsing.")

uploaded_file = st.file_uploader("Upload PDF Tickets", type="pdf")

if uploaded_file:
    if st.button("🚀 Process Tickets"):
        with st.spinner("Converting PDF..."):
            images = convert_from_bytes(uploaded_file.read(), dpi=200)
        
        all_rows = []
        progress_bar = st.progress(0)
        
        for i, img in enumerate(images):
            with st.spinner(f"AI analyzing page {i+1} of {len(images)}..."):
                raw_text = get_ai_data(img)
                if "ERROR" in raw_text:
                    st.error(raw_text)
                    break
                
                parsed = extract_logic(raw_text)
                all_rows.append(build_row(parsed))
                progress_bar.progress((i + 1) / len(images))

        if all_rows:
            cols = ["Date", "Ticket", "Truck ID", "Driver", "Measure", "S35", "S80", "S150", "S175", "S250", "SubTotal", "G1", "G2", "T40", "T100", "T175", "T200", "T275", "TLMTotal"]
            df = pd.DataFrame(all_rows, columns=cols)
            st.success("Extraction Complete.")
            st.dataframe(df)

            csv_io = io.StringIO()
            csv_io.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\nProject Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\nDate,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
            df.to_csv(csv_io, index=False, header=False)
            st.download_button("📥 Download Final Master Log", csv_io.getvalue(), "MasterLog_Final.csv")
