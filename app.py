import streamlit as st
import pandas as pd
import re
import io
from pdf2image import convert_from_bytes
import pytesseract

st.set_page_config(page_title="Scanned Ticket Processor", layout="wide")

def find_val(text, patterns):
    """Safely find a value using multiple regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                # Try to return the first captured group ()
                return match.group(1).strip()
            except IndexError:
                # If no () group exists, return the whole match
                return match.group(0).strip()
    return ""

def process_scanned_pdf(pdf_bytes):
    all_rows = []
    # dpi=600 is very high quality but slower. 
    # Use thread_count=2 to help the Streamlit server process faster.
    images = convert_from_bytes(pdf_bytes, dpi=600)
    
    for i, image in enumerate(images):
        # OCR the page
        text = pytesseract.image_to_string(image)
        
        # --- EXTRACTION LOGIC (Optimized for OCR) ---
        # 1. Ticket ID: Look for 9-10 digits at the top
        ticket_id = find_val(text, [r'(\d{9,10})'])
        
        # 2. Date: Look for MM/DD/YYYY
        date = find_val(text, [r'(\d{2}/\d{2}/\d{4})'])
        
        # 3. Truck ID: Look for Crew or use known Truck ID 848117
        truck = find_val(text, [r'Crew\s*[:\s]*(\d+)', r'(848117)'])
        
        # 4. Driver/Supervisor
        driver = find_val(text, [r'Supervisor\s*[:\s]*([A-Z\s]+)', r'(Fernando)'])
        driver = driver.split('\n')[0].strip() # Clean up any trailing OCR junk
        
        # 5. Hazard Type
        h_type = "HANGER" if "HANGER" in text.upper() else "LEANER"
        
        # 6. Measure (The diameter)
        measure_str = find_val(text, [r'Measure\s*[:\s]*([\d.]+)'])
        
        try:
            m = float(measure_str) if measure_str else 0.0
        except:
            m = 0.0

        # --- CSV MAPPING (19 Columns) ---
        row = [" $- " for _ in range(19)]
        row[0], row[1], row[2], row[3] = date, ticket_id, truck, driver
        row[11], row[12] = "", "" # Formatting gaps

        if h_type == "HANGER":
            row[4] = "1"
            row[5], row[10], row[13], row[18] = " $35.00 ", " $35.00 ", " $40.00 ", " $40.00 "
        else:
            row[4] = str(m)
            # Ranges defined by your Master Log headers
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
st.write("Reading high-DPI scans and generating Master Log CSV.")

uploaded_file = st.file_uploader("Upload Scanned PDF", type="pdf")

if uploaded_file:
    with st.spinner('Performing high-quality OCR... this takes about 15-30 seconds per page.'):
        file_bytes = uploaded_file.read()
        data = process_scanned_pdf(file_bytes)
        
        if not data:
            st.error("No valid tickets detected. Try checking if the PDF is oriented correctly.")
        else:
            st.success(f"Success! Processed {len(data)} tickets.")
            
            # Display Headers
            display_cols = [
                "Date", "Ticket", "Truck ID", "Driver", "Measure", 
                "Sub $35", "Sub $80", "Sub $150", "Sub $175", "Sub $250", "Sub Total",
                "Gap1", "Gap2", 
                "TLM $40", "TLM $100", "TLM $175", "TLM $200", "TLM $275", "TLM Total"
            ]
            
            df = pd.DataFrame(data, columns=display_cols)
            st.dataframe(df)

            # Generate downloadable CSV
            output = io.StringIO()
            output.write('Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\n')
            output.write('Project Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\n')
            output.write('Date,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\n')
            
            df.to_csv(output, index=False, header=False)
            
            st.download_button(
                label="📥 Download Master Log CSV",
                data=output.getvalue(),
                file_name="MasterLog_Output.csv",
                mime="text/csv"
            )
