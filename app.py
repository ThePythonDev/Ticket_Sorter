import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import json
import time

st.set_page_config(page_title="AI Ticket Processor Pro", layout="wide")

# Sidebar for API Key
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Enter Google AI API Key", type="password")
    st.info("Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)")
    model_choice = st.selectbox("Select Model", ["gemini-1.5-flash", "gemini-1.5-pro"])

def process_with_ai(pdf_file, key, model_name):
    genai.configure(api_key=key)
    
    # 1. Save uploaded file to a temporary location for the Google File API
    with open("temp_tickets.pdf", "wb") as f:
        f.write(pdf_file.getbuffer())

    # 2. Upload to Google File API
    st.info("Uploading PDF to Google AI Engine...")
    uploaded_file = genai.upload_file(path="temp_tickets.pdf", mime_type="application/pdf")
    
    # 3. Wait for the file to be processed by Google
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = genai.get_file(uploaded_file.name)

    # 4. Generate Content
    model = genai.GenerativeModel(model_name)
    prompt = """
    Instructions:
    1. Scan every page of this PDF. Each page is a Hazard Ticket.
    2. Extract data from EVERY ticket found.
    3. Return the data ONLY as a valid JSON list. 
    4. If a value is unreadable, use an empty string.

    Fields to extract:
    - date: Format MM/DD/YYYY
    - ticket_id: The large printed number at the top
    - truck_id: The number listed after 'Crew:' (usually 848117)
    - driver: The name listed after 'Supervisor:' or 'Driver:' (e.g., Fernando)
    - type: Must be 'HANGER' or 'LEANER'
    - measure: The numeric diameter value next to 'Measure:'

    Example JSON output:
    [{"date": "02/25/2026", "ticket_id": "114890527", "truck_id": "848117", "driver": "Fernando", "type": "HANGER", "measure": 3.25}]
    """

    response = model.generate_content([prompt, uploaded_file])
    
    # Cleanup: Delete the file from Google's server
    genai.delete_file(uploaded_file.name)
    
    # Parse JSON
    text_response = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text_response)

def generate_master_log(data):
    rows = []
    for item in data:
        # Standard row with 19 columns initialized to " $- "
        row = [" $- " for _ in range(19)]
        row[0] = item.get('date', "")
        row[1] = item.get('ticket_id', "")
        row[2] = item.get('truck_id', "")
        row[3] = item.get('driver', "")
        row[11], row[12] = "", "" # Formatting Gaps

        h_type = str(item.get('type', "")).upper()
        try:
            # Handle cases where measure might have text
            m_str = str(item.get('measure', '0')).replace('"', '').strip()
            m = float(m_str)
        except:
            m = 0.0

        if "HANGER" in h_type:
            row[4] = "1"
            row[5], row[10], row[13], row[18] = " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
        else:
            row[4] = str(m)
            # Ranges defined by your Master Log
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
st.title("🌲 Debris Ticket AI Processor")
st.markdown("Uses Google Gemini to accurately read scanned tickets and generate your Master Log.")

uploaded_file = st.file_uploader("Upload Scanned PDF", type="pdf")

if uploaded_file:
    if not api_key:
        st.warning("Please enter your Google API Key in the sidebar.")
    else:
        if st.button("🚀 Run AI Analysis"):
            with st.spinner("AI is analyzing handwriting and stamps..."):
                try:
                    raw_results = process_with_ai(uploaded_file, api_key, model_choice)
                    formatted_rows = generate_master_log(raw_results)
                    
                    st.success(f"Processed {len(formatted_rows)} tickets!")
                    
                    # Columns for display
                    display_cols = ["Date", "Ticket", "Truck ID", "Driver", "Measure/Type", "Sub $35", "Sub $80", "Sub $150", "Sub $175", "Sub $250", "Sub Total", "Gap1", "Gap2", "TLM $40", "TLM $100", "TLM $175", "TLM $200", "TLM $275", "TLM Total"]
                    df = pd.DataFrame(formatted_rows, columns=display_cols)
                    st.dataframe(df)

                    # Create CSV
                    csv_io = io.StringIO()
                    csv_io.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
                    csv_io.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
                    df.to_csv(csv_io, index=False, header=False)
                    
                    st.download_button(
                        label="📥 Download Master Log CSV",
                        data=csv_io.getvalue(),
                        file_name="MasterLog_AI_Output.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
