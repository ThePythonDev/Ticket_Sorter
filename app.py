import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

st.set_page_config(page_title="Hazard Ticket Processor", layout="wide")

def find_val(text, patterns):
    """Try multiple patterns to find a value."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def process_pdf(pdf_file):
    all_rows = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # --- EXTRACTION LOGIC ---
            # Using multiple regex options for better reliability
            ticket_id = find_val(text, [r'^(\d{9,10})', r'Ticket\s*#?\s*:?\s*(\d{9,10})'])
            date = find_val(text, [r'(\d{2}/\d{2}/\d{4})'])
            truck = find_val(text, [r'Crew\s*:\s*(\w+)', r'Truck\s*ID\s*:\s*(\w+)'])
            driver = find_val(text, [r'Supervisor\s*:\s*([\w\s]+?)(?=\n)', r'Driver\s*:\s*([\w\s]+?)(?=\n)'])
            h_type = find_val(text, [r'Hazard Type\s*:\s*(\w+)'])
            measure_str = find_val(text, [r'Measure\s*:\s*([\d.]+)'])
            
            # Fallback for driver if it captures too much
            driver = driver.split('\n')[0].strip()

            try:
                m = float(measure_str) if measure_str else 0.0
            except:
                m = 0.0
            
            # --- CSV ROW MAPPING (19 Columns) ---
            row = ["" for _ in range(19)]
            row[0], row[1], row[2], row[3] = date, ticket_id, truck, driver
            
            # Logic for sorting into Ranges
            if "HANGER" in h_type.upper():
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
            
            # Only add the row if we at least found a Ticket ID
            if ticket_id:
                all_rows.append(row)
            
    return all_rows

# --- WEB UI ---
st.title("🌲 Hazard Ticket to Master Log")
st.markdown("Upload the PDF tickets. The app will extract the data and format it into the Master Log CSV structure.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    data = process_pdf(uploaded_file)
    
    if not data:
        st.error("❌ No data could be extracted. The PDF might be a scan (image) rather than text. Try a different PDF or check 'Debug Info' below.")
        
        with st.expander("🔍 Debug Info (See what the computer reads)"):
            with pdfplumber.open(uploaded_file) as p:
                raw_text = p.pages[0].extract_text()
                st.text(raw_text if raw_text else "No text found on Page 1.")
    else:
        st.success(f"✅ Successfully processed {len(data)} tickets!")
        
        # Headers
        cols = ["Date","Ticket","Truck ID","Driver Name","1= HANGER / LEANER DIAMETER","$35.00","$80.00","$150.00","$175.00","$250.00","Sub Total","","","$40.00","$100.00","$175.00","$200.00","$275.00","TLM Total"]
        df = pd.DataFrame(data, columns=cols)
        
        st.dataframe(df)

        # Generate CSV
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
