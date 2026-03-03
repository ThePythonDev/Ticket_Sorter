import streamlit as st
import pandas as pd
import re
import io
from pdf2image import convert_from_bytes
import pytesseract

st.set_page_config(page_title="Ticket Processor", layout="wide")

def find_val(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def process_scanned_pdf(pdf_bytes):
    all_rows = []
    # dpi=200 is a good balance between speed and OCR accuracy
    images = convert_from_bytes(pdf_bytes, dpi=600)
    
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        
        # --- EXTRACTION LOGIC ---
        # Look for the Ticket ID (the big number at the top)
        ticket_id = find_val(text, [r'(\d{9,10})'])
        date = find_val(text, [r'(\d{2}/\d{2}/\d{4})'])
        truck = find_val(text, [r'Crew\s*[:\s]*(\w+)', r'848117'])
        driver = find_val(text, [r'Supervisor\s*[:\s]*([\w\s]+)', r'Fernando'])
        
        driver = driver.split('\n')[0].strip()
        h_type = "HANGER" if "HANGER" in text.upper() else "LEANER"
        measure_str = find_val(text, [r'Measure\s*[:\s]*([\d.]+)'])
        
        try:
            m = float(measure_str) if measure_str else 0.0
        except:
            m = 0.0

        # Initialize row with empty money slots " $- "
        row = [" $- " for _ in range(19)]
        row[0], row[1], row[2], row[3] = date, ticket_id, truck, driver
        row[11], row[12] = "", "" # The gap columns

        if h_type == "HANGER":
            row[4] = "1"
            row[5], row[10], row[13], row[18] = " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
        else:
            row[4] = str(m)
            # Sorting logic based on your ranges
            if 0.01 <= m <= 23.99:
                row[6], row[10], row[14], row[18] = " $80.00 ", " $80.00 ", " $100.00 ", " $100.00 "
            elif 24.0 <= m <= 35.99:
                row[7], row[10], row[15], row[18] = " $150.00 ", " $150.00 ", " $175.00 ", " $175.00 "
            elif 36.0 <= m <= 47.99:
                row[8], row[10], row[16], row[18] = " $175.00 ", " $175.00 ", " $200.00 ", " $200.00 "
            elif m >= 48.0:
                row[9], row[10], row[17], row[18] = " $250.00 ", " $250.00 ", " $275.00 ", " $275.00 "
        
        if ticket_id:
            all_rows.append(row)
            
    return all_rows

st.title("📸 Scanned Ticket to Master Log")
st.write("Upload scanned PDFs to extract data into the Master Log format.")

uploaded_file = st.file_uploader("Upload Scanned PDF", type="pdf")

if uploaded_file:
    with st.spinner('Converting PDF to Images and performing OCR...'):
        file_bytes = uploaded_file.read()
        data = process_scanned_pdf(file_bytes)
        
        if not data:
            st.error("No ticket IDs found. Please check if the scan is readable.")
        else:
            st.success(f"Processed {len(data)} tickets!")
            
            # UNIQUE display names to avoid the "Duplicate Column" error
            display_cols = [
                "Date", "Ticket", "Truck ID", "Driver", "Measure", 
                "Sub $35", "Sub $80", "Sub $150", "Sub $175", "Sub $250", "Sub Total",
                "Gap1", "Gap2", 
                "TLM $40", "TLM $100", "TLM $175", "TLM $200", "TLM $275", "TLM Total"
            ]
            
            df = pd.DataFrame(data, columns=display_cols)
            st.dataframe(df)

            # Build the CSV for download
            output = io.StringIO()
            output.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
            output.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
            # The exact header line for Excel:
            output.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
            
            # Export data without the temp display headers
            df.to_csv(output, index=False, header=False)
            
            st.download_button(
                label="📥 Download Master Log CSV",
                data=output.getvalue(),
                file_name="MasterLog_Output.csv",
                mime="text/csv"
            )
