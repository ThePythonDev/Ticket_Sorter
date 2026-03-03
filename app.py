import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

st.set_page_config(page_title="Hazard Ticket Processor", layout="wide")

def find_val(text, pattern):
    match = re.search(pattern, text)
    return match.group(1) if match else ""

def process_pdf(pdf_file):
    all_rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            # Extract Fields
            ticket_id = find_val(text, r'(\d{9,10})')
            date = find_val(text, r'Date/Time:\s+(\d{2}/\d{2}/\d{4})')
            truck = find_val(text, r'Crew:\s+(\w+)')
            driver = find_val(text, r'Supervisor:\s+(\w+)')
            h_type = find_val(text, r'Hazard Type:\s+(\w+)')
            measure_str = find_val(text, r'Measure:\s+([\d.]+)')
            
            m = float(measure_str) if measure_str else 0.0
            
            # Create the 19-column row (Matches your CSV)
            row = ["" for _ in range(19)]
            row[0], row[1], row[2], row[3] = date, ticket_id, truck, driver
            
            if "HANGER" in h_type.upper():
                row[4] = "1"
                row[5], row[10] = " $35.00 ", " $35.00 " # Sub
                row[13], row[18] = " $40.00 ", " $40.00 " # TLM
            else:
                row[4] = str(m)
                if 1.1 <= m <= 23.99:
                    row[6], row[10], row[14], row[18] = " $80.00 ", " $80.00 ", " $100.00 ", " $100.00 "
                elif 24.0 <= m <= 35.99:
                    row[7], row[10], row[15], row[18] = " $150.00 ", " $150.00 ", " $175.00 ", " $175.00 "
                elif 36.0 <= m <= 47.99:
                    row[8], row[10], row[16], row[18] = " $175.00 ", " $175.00 ", " $200.00 ", " $200.00 "
                elif m >= 48.0:
                    row[9], row[10], row[17], row[18] = " $250.00 ", " $250.00 ", " $275.00 ", " $275.00 "
            
            all_rows.append(row)
    return all_rows

# --- WEB UI ---
st.title("🌲 Hazard Ticket to Master Log")
st.write("Upload your PDF tickets to generate the formatted CSV.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Processing tickets...'):
        data = process_pdf(uploaded_file)
        
        if data:
            # Create DataFrame
            cols = ["Date","Ticket","Truck ID","Driver Name","1= HANGER / LEANER DIAMETER","$35.00","$80.00","$150.00","$175.00","$250.00","Sub Total","","","$40.00","$100.00","$175.00","$200.00","$275.00","TLM Total"]
            df = pd.DataFrame(data, columns=cols)
            
            # Show preview
            st.success(f"Processed {len(data)} tickets!")
            st.dataframe(df.head())

            # Convert to CSV string with headers
            output = io.StringIO()
            output.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
            output.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
            df.to_csv(output, index=False)
            
            st.download_button(
                label="📥 Download Master Log CSV",
                data=output.getvalue(),
                file_name="MasterLog_Output.csv",
                mime="text/csv"
            )
