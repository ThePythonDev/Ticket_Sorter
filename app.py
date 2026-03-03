import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import io
import json
import re

st.set_page_config(page_title="AI Ticket Processor", layout="wide")

# Sidebar for API Key
with st.sidebar:
    st.title("Settings")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Get your key at [aistudio.google.com](https://aistudio.google.com/app/apikey)")
    # Using gemini-2.0-flash for high-speed OCR and accuracy
    model_id = "gemini-2.0-flash" 

def process_with_ai(uploaded_file, api_key):
    client = genai.Client(api_key=api_key)
    
    # Read the file into bytes
    file_bytes = uploaded_file.getvalue()
    
    prompt = """
    Extract data from every Hazard Ticket in this PDF. 
    Return ONLY a JSON list of objects.
    
    Fields:
    - date: MM/DD/YYYY
    - ticket_id: Number at the top
    - truck_id: The 'Crew' number (e.g., 848117)
    - driver: The 'Supervisor' or 'Driver' name
    - type: 'HANGER' or 'LEANER'
    - measure: Numeric diameter (e.g. 12.25)
    
    Example: [{"date": "02/25/2026", "ticket_id": "114890527", "truck_id": "848117", "driver": "Fernando", "type": "HANGER", "measure": 1.0}]
    """

    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    types.Part.from_text(text=prompt),
                ],
            ),
        ],
        config=types.GenerateContentConfig(
            # Thinking is disabled here for speed/cost, Flash handles this task well
            temperature=0.1, 
        ),
    )
    
    # Clean output
    text = response.text
    json_str = re.search(r'\[.*\]', text, re.DOTALL).group()
    return json.loads(json_str)

def format_master_log(data):
    rows = []
    for item in data:
        row = [" $- " for _ in range(19)]
        row[0] = item.get('date', "")
        row[1] = item.get('ticket_id', "")
        row[2] = item.get('truck_id', "")
        row[3] = item.get('driver', "")
        row[11], row[12] = "", "" # Gaps

        h_type = str(item.get('type', "")).upper()
        try:
            m = float(item.get('measure', 0))
        except:
            m = 0.0

        if "HANGER" in h_type:
            row[4] = "1"
            row[5], row[10], row[13], row[18] = " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
        else:
            row[4] = str(m)
            # Master Log Range Logic
            if 0.01 <= m <= 23.99:
                row[6], row[10], row[14], row[18] = " $80.00 ", " $80.00 ", " $100.00 ", " $100.00 "
            elif 24.0 <= m <= 35.99:
                row[7], row[10], row[15], row[18] = " $150.00 ", " $150.00 ", " $175.00 ", " $175.00 "
            elif 36.0 <= m <= 47.99:
                row[8], row[10], row[16], row[18] = " $175.00 ", " $175.00 ", " $200.00 ", " $200.00 "
            elif m >= 48.0:
                row[9], row[10], row[17], row[18] = " $250.00 ", " $250.00 ", " $275.00 ", " $275.00 "
        rows.append(row)
    return rows

# --- APP UI ---
st.title("📄 AI Master Log Generator")
st.write("Upload scanned tickets. AI will extract data, Python will calculate ranges.")

uploaded_file = st.file_uploader("Upload PDF Tickets", type="pdf")

if uploaded_file:
    if not user_api_key:
        st.warning("Please enter your API Key in the sidebar.")
    else:
        if st.button("🚀 Process Tickets"):
            with st.spinner("AI is analyzing the PDF..."):
                try:
                    raw_data = process_with_ai(uploaded_file, user_api_key)
                    final_rows = format_master_log(raw_data)
                    
                    st.success(f"Extracted {len(final_rows)} tickets!")
                    
                    # Columns for web preview
                    cols = ["Date", "Ticket", "Truck ID", "Driver", "Measure", "Sub 35", "Sub 80", "Sub 150", "Sub 175", "Sub 250", "Sub Total", "G1", "G2", "TLM 40", "TLM 100", "TLM 175", "TLM 200", "TLM 275", "TLM Total"]
                    df = pd.DataFrame(final_rows, columns=cols)
                    st.dataframe(df)

                    # Export to CSV
                    csv_io = io.StringIO()
                    csv_io.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
                    df.to_csv(csv_io, index=False, header=False)
                    
                    st.download_button("📥 Download Master Log CSV", csv_io.getvalue(), "MasterLog.csv", "text/csv")
                except Exception as e:
                    st.error(f"Error: {e}")
