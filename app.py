import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import io
import json
import re

st.set_page_config(page_title="AI Ticket Master Log", layout="wide")

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("AI Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    
    # We provide multiple model options. 
    # '2.0-flash-lite' is currently the best for free-tier OCR stability.
    model_choice = st.selectbox(
        "Select Model",
        [
            "gemini-2.0-flash-lite-preview-02-05", 
            "gemini-2.0-flash", 
            "gemini-1.5-flash"
        ],
        help="If you get a 429 error, try the 'Lite' or '1.5' version."
    )
    
    st.markdown("[Get a free API Key](https://aistudio.google.com/app/apikey)")

# --- LOGIC FUNCTIONS ---
def call_gemini_ai(pdf_file, key, model_id):
    client = genai.Client(api_key=key)
    file_bytes = pdf_file.getvalue()
    
    # This prompt is tuned for debris tickets
    prompt = """
    Return a JSON list of objects for every ticket in this PDF.
    Required fields:
    - date: MM/DD/YYYY
    - ticket_id: Large number at top
    - truck_id: Number after 'Crew:'
    - driver: Name after 'Supervisor:'
    - type: 'HANGER' or 'LEANER'
    - measure: Numeric value after 'Measure:' (e.g. 12.5)
    
    Return ONLY valid JSON code. No conversation.
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
            temperature=0.1,
            # We skip 'Thinking' for standard OCR to stay within free tier limits
        ),
    )
    
    # Regex to pull JSON out of the response safely
    text_resp = response.text
    json_match = re.search(r'\[.*\]', text_resp, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return None

def process_to_csv_format(data):
    rows = []
    for item in data:
        # Initialize row with 19 columns and " $- " for empty money slots
        row = [" $- " for _ in range(19)]
        row[0] = item.get('date', "")
        row[1] = item.get('ticket_id', "")
        row[2] = item.get('truck_id', "")
        row[3] = item.get('driver', "")
        row[11], row[12] = "", "" # Formatting Gaps

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
            # Standard Master Log Range Sorting
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
st.title("🌲 Scanned Ticket AI Master Log")
st.write("Convert your scanned PDF tickets into a formatted Master Log using Gemini AI.")

file = st.file_uploader("Upload PDF Tickets", type="pdf")

if file:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar to begin.")
    else:
        if st.button("🚀 Generate Master Log"):
            with st.spinner(f"AI is analyzing with {model_choice}..."):
                try:
                    raw_data = call_gemini_ai(file, api_key, model_choice)
                    if raw_data:
                        final_rows = process_to_csv_format(raw_data)
                        
                        st.success(f"Extracted {len(final_rows)} tickets!")
                        
                        # Preview Table
                        cols = ["Date", "Ticket", "Truck ID", "Driver", "Measure", "Sub 35", "Sub 80", "Sub 150", "Sub 175", "Sub 250", "Sub Total", "G1", "G2", "TLM 40", "TLM 100", "TLM 175", "TLM 200", "TLM 275", "TLM Total"]
                        df = pd.DataFrame(final_rows, columns=cols)
                        st.dataframe(df)

                        # Create the download file
                        csv_output = io.StringIO()
                        csv_output.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
                        csv_output.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
                        csv_output.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
                        df.to_csv(csv_output, index=False, header=False)
                        
                        st.download_button(
                            "📥 Download CSV for Excel", 
                            csv_output.getvalue(), 
                            "MasterLog_Output.csv", 
                            "text/csv"
                        )
                    else:
                        st.error("AI failed to return structured data. Check your PDF quality.")
                except Exception as e:
                    if "429" in str(e):
                        st.error("Rate limit exceeded. Switch the 'Select Model' to a different version in the sidebar and try again.")
                    else:
                        st.error(f"Error: {e}")
