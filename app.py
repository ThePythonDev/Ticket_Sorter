import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Glyphon", layout="wide")
st.write("© Copyright Soren Clink 2026 all rights reserved")
st.title("Glyphon Ticket Proccesser")
st.write("Only one or two poeple should be using the app at a time do to streamlit limits")
st.write("Process scanned tickets via Puter.js AI.")
st.write("Please take note that accuracy is 97%")
st.write("(Double checking tickets is reccomended for complete accuracy)")
st.write("Please contact Soren Clink at sorenclink@gmail.com if any errors occur")
st.markdown("""
---
### Instructions:
1. Select your PDF file in the box above.
2. Click **Start AI Analysis**.
3. Wait for the success message.
4. Click the blue **Download CSV spreadsheet** button to save your file.
""")
# This is the full JS/HTML engine
puter_component = """
<div id="puter-root" style="background-color: #0e1117; color: white; padding: 20px; font-family: sans-serif; border-radius: 10px; border: 1px solid #30363d;">
    <script src="https://js.puter.com/v2/"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    
    <div style="text-align: center; border: 2px dashed #444; padding: 30px; border-radius: 10px; background: #161b22;">
        <input type="file" id="pdf-file" accept="application/pdf" style="margin-bottom: 15px; color: #8b949e;"><br>
        <button id="process-btn" style="background-color: #238636; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px;">
            Start AI Analysis
        </button>
    </div>
    
    <p id="status" style="color: #e3b341; margin-top: 15px; font-weight: bold;"></p>
    
    <div id="download-container" style="display: none; margin-top: 20px; padding: 20px; background: #21262d; border-radius: 8px; text-align: center;">
        <p style="margin-bottom: 15px; color: #7ee787;">✅ Analysis Complete!</p>
        <button id="download-csv-btn" style="background-color: #1f6feb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
            Download CSV spreadsheet
        </button>
    </div>

    <details style="margin-top: 20px; cursor: pointer;">
        <summary style="color: #8b949e; font-size: 13px;">View Raw AI Data (JSON)</summary>
        <pre id="output" style="background: #000; padding: 15px; font-size: 12px; max-height: 250px; overflow-y: auto; border-radius: 6px; margin-top: 10px; border: 1px solid #30363d; color: #d1d5da;"></pre>
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
            status.innerText = "❌ Please select a PDF file first.";
            return;
        }

        processBtn.disabled = true;
        processBtn.style.opacity = "0.5";
        downloadContainer.style.display = "none";
        processedData = [];
        
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = async function() {
            try {
                const typedarray = new Uint8Array(this.result);
                const pdf = await pdfjsLib.getDocument(typedarray).promise;
                
                for (let i = 1; i <= pdf.numPages; i++) {
                    status.innerText = `AI is analyzing page ${i} of ${pdf.numPages}...`;
                    
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

            } catch (err) {
                status.innerText = "❌ Error processing PDF. See console.";
                console.error(err);
                processBtn.disabled = false;
                processBtn.style.opacity = "1";
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
            row[11] = ""; row[12] = ""; // The two blank gap columns

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
        link.setAttribute("download", "_generated.csv");
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
</script>
"""

# Render the component
components.html(puter_component, height=700, scrolling=True)
