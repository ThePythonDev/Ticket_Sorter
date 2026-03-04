import streamlit as st
import streamlit.components.v1 as components

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
    </style>
    """, unsafe_allow_html=True)

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
    st.write("If you run into any issues, I am always happy to help!")
    st.caption("sorenclink@gmail.com")
    
    st.divider()
    st.markdown('<p class="footer-text">© 2026 Soren Clink<br>All rights reserved.</p>', unsafe_allow_html=True)

# --- MAIN INTERFACE ---
st.title("Glyphon")
st.markdown("Upload your scanned PDF tickets below. AI will read the tickets and prepare a CSV.")

# Process Steps
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Step 1", "Upload PDF")
with col2:
    st.metric("Step 2", "AI Review")
with col3:
    st.metric("Step 3", "Download CSV")

st.divider()

# --- THE PROCESSING ENGINE ---
puter_component = """
<div id="puter-root" style="background-color: #161b22; color: #e6edf3; padding: 30px; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-radius: 12px; border: 1px solid #30363d;">
    <script src="https://js.puter.com/v2/"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    
    <div style="text-align: center; border: 2px dashed #484f58; padding: 40px; border-radius: 12px; background: #0d1117;">
        <p style="margin-top: 0; font-size: 16px; color: #c9d1d9;">Select the PDF file you'd like to process</p>
        <input type="file" id="pdf-file" accept="application/pdf" style="margin-bottom: 25px; color: #8b949e;"><br>
        <button id="process-btn" style="background-color: #238636; color: white; border: none; padding: 14px 40px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 16px; box-shadow: 0 2px 0 rgba(0,0,0,0.2);">
            Analyze PDF Tickets
        </button>
    </div>
    
    <div id="status-area" style="margin-top: 25px; text-align: center;">
        <p id="status" style="color: #d29922; font-size: 15px; font-weight: 500;"></p>
    </div>
    
    <div id="download-container" style="display: none; margin-top: 25px; padding: 25px; background: rgba(56, 139, 253, 0.1); border-radius: 12px; text-align: center; border: 1px solid #388bfd;">
        <p style="margin: 0 0 15px 0; color: #58a6ff; font-weight: 600; font-size: 16px;">Success! Your data is ready for export.</p>
        <button id="download-csv-btn" style="background-color: #1f6feb; color: white; border: none; padding: 12px 28px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 15px;">
            Download CSV Spreadsheet
        </button>
    </div>

    <details style="margin-top: 30px; border-top: 1px solid #30363d; padding-top: 20px;">
        <summary style="color: #8b949e; font-size: 13px; cursor: pointer; opacity: 0.8;">Data Preview (Raw JSON)</summary>
        <pre id="output" style="background: #010409; padding: 15px; font-size: 12px; max-height: 200px; overflow-y: auto; border-radius: 8px; margin-top: 10px; border: 1px solid #30363d; color: #7ee787;"></pre>
    </details>
</div>

<script>
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
    
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const processBtn = document.getElementById('process-btn');
    const downloadContainer = document.getElementById('download-container');
    const downloadCsvBtn = document.getElementById('download-csv-btn');
    
    let processedData = [];

    processBtn.onclick = async () => {
        const fileInput = document.getElementById('pdf-file');
        if (!fileInput.files.length) {
            status.innerText = "Please select a PDF file to begin.";
            return;
        }

        processBtn.disabled = true;
        processBtn.style.opacity = "0.6";
        processBtn.innerText = "Reading file...";
        downloadContainer.style.display = "none";
        processedData = [];
        
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = async function() {
            try {
                const typedarray = new Uint8Array(this.result);
                const pdf = await pdfjsLib.getDocument(typedarray).promise;
                
                for (let i = 1; i <= pdf.numPages; i++) {
                    status.innerHTML = `Processing page ${i} of ${pdf.numPages}...`;
                    
                    const page = await pdf.getPage(i);
                    const viewport = page.getViewport({scale: 2.0});
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    await page.render({canvasContext: context, viewport: viewport}).promise;
                    
                    const base64Image = canvas.toDataURL('image/jpeg', 0.8);

                    const response = await puter.ai.chat(
                        "Extract debris ticket info. Return ONLY a JSON object: {\\"date\\":\\"MM/DD/YYYY\\", \\"id\\":\\"number\\", \\"type\\":\\"HANGER/LEANER\\", \\"measure\\": 0.0}",
                        base64Image
                    );
                    
                    const cleanJson = response.message.content.replace(/```json|```/g, "").trim();
                    processedData.push(JSON.parse(cleanJson));
                }

                status.innerText = "";
                output.innerText = JSON.stringify(processedData, null, 2);
                downloadContainer.style.display = "block";
                processBtn.disabled = false;
                processBtn.style.opacity = "1";
                processBtn.innerText = "Analyze PDF Tickets";

            } catch (err) {
                status.innerText = "We hit a snag reading the PDF. Please try again or check the file.";
                console.error(err);
                processBtn.disabled = false;
                processBtn.style.opacity = "1";
                processBtn.innerText = "Retry Analysis";
            }
        };
        reader.readAsArrayBuffer(file);
    };

    downloadCsvBtn.onclick = () => {
        let csv = "Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\\nProject Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\\nDate,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\\n";
        
        processedData.forEach(item => {
            let row = Array(19).fill(" $- ");
            row[0] = item.date || ""; 
            row[1] = item.id || ""; 
            row[2] = "848117"; 
            row[3] = "Fernando";
            row[11] = ""; row[12] = ""; 

            let m = parseFloat(item.measure) || 0;
            let type = (item.type || "").toUpperCase();

            if (type.includes("HANGER")) {
                row[4] = "1";
                row[5] = " $35.00 "; row[10] = " $35.00 "; 
                row[13] = " $40.00 "; row[18] = " $40.00 ";
            } else {
                row[4] = m.toString();
                if (m > 0 && m <= 23.99) { 
                    row[6] = " $80.00 "; row[10] = " $80.00 "; 
                    row[14] = " $100.00 "; row[18] = " $100.00 "; 
                }
                else if (m >= 24 && m <= 35.99) { 
                    row[7] = " $150.00 "; row[10] = " $150.00 "; 
                    row[15] = " $175.00 "; row[18] = " $175.00 "; 
                }
                else if (m >= 36 && m <= 47.99) { 
                    row[8] = " $175.00 "; row[10] = " $175.00 "; 
                    row[16] = " $200.00 "; row[18] = " $200.00 "; 
                }
                else if (m >= 48) { 
                    row[9] = " $250.00 "; row[10] = " $250.00 "; 
                    row[17] = " $275.00 "; row[18] = " $275.00 "; 
                }
            }
            csv += row.join(",") + "\\n";
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", `Processed_Tickets_Export.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
</script>
"""

# Render the component
components.html(puter_component, height=750, scrolling=True)
