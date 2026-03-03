import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import io
import json
import re
import time

st.set_page_config(page_title="AI Ticket Processor", layout="wide")

# Sidebar for API Key and Model Selection
with st.sidebar:
    st.title("Settings")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)")
    
    # gemini-1.5-flash has the highest free quota
    model_id = st.selectbox("Select Model", 
                            ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
                            index=0)

def process_with_ai(uploaded_file, api_key, selected_model):
    client = genai.Client(api_key=api_key)
    file_bytes = uploaded_file.getvalue()
    
    prompt = """
    Extract data from every Hazard Ticket in this PDF. 
    Return ONLY a JSON list of objects.
    
    Fields:
    - date: MM/DD/YYYY
    - ticket_id: Large number at the top
    - truck_id: The 'Crew' number (usually 848117)
    - driver: The 'Supervisor' or 'Driver' name
    - type: 'HANGER' or 'LEANER'
    - measure: Numeric diameter (e.g. 12.25)
    
    Return format: [{"date": "MM/DD/YYYY", "ticket_id": "...", "truck_id": "...", "driver": "...", "type": "...", "measure": 0.0}]
    """

    try:
        response = client.models.generate_content(
            model=selected_model,
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
                temperature=0.1,
            ),
        )
        
        # Extract JSON from the response text
        text = response.text
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            st.error("AI returned text but no JSON list found. AI Response: " + text)
            return None
            
    except Exception as e:
        if "429" in str(e):
            st.error("Rate Limit Reached (429). Please wait 30 seconds and try again, or switch to the 'gemini-1.5-flash' model in the sidebar.")
        else:
            st.error(f"AI Error: {e}")
        return None

def format_master_log(data):
    rows = []
    for item in data:
        row = [" $- " for _ in range(19)]
        row[0] = item.get('date', "")
        row[1] = item.get('ticket_id', "")
        row[2] = item.get('truck_id', "")
        row[3] = item.get('driver', "")
        row[11], row[12] = "", "" 

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

# --- UI ---
st.title("📄 AI Master Log Generator")
st.write("Upload scanned tickets. AI extracts data, Python calculates ranges.")

uploaded_file = st.file_uploader("Upload PDF Tickets", type="pdf")

if uploaded_file:
    if not user_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar.")
    else:
        if st.button("🚀 Process Tickets"):
            with st.spinner(f"AI ({model_id}) is analyzing the PDF..."):
                raw_data = process_with_ai(uploaded_file, user_api_key, model_id)
                
                if raw_data:
                    final_rows = format_master_log(raw_data)
                    st.success(f"Extracted {len(final_rows)} tickets!")
                    
                    cols = ["Date", "Ticket", "Truck ID", "Driver", "Measure", "Sub 35", "Sub 80", "Sub 150", "Sub 175", "Sub 250", "Sub Total", "G1", "G2", "TLM 40", "TLM 100", "TLM 175", "TLM 200", "TLM 275", "TLM Total"]
                    df = pd.DataFrame(final_rows, columns=cols)
                    st.dataframe(df)

                    csv_io = io.StringIO()
                    csv_io.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
                    df.to_csv(csv_io, index=False, header=False)
                    
                    st.download_button("📥 Download Master Log CSV", csv_io.getvalue(), "MasterLog.csv", "text/csv")
