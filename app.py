import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io

st.set_page_config(page_title="Puter AI Ticket Processor", layout="wide")

st.title("🌲 Puter.js + Streamlit: Ticket AI")
st.write("This app uses Puter's browser-based AI to process scanned tickets.")

# 1. We create the JavaScript/HTML logic for Puter.js
# This will be embedded as an iframe inside Streamlit
puter_component = """
<div id="puter-root" style="background-color: #1e1e1e; color: white; padding: 20px; font-family: sans-serif; border-radius: 10px;">
    <script src="https://js.puter.com/v2/"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
    
    <div style="text-align: center; border: 2px dashed #444; padding: 20px;">
        <input type="file" id="pdf-file" accept="application/pdf" style="margin-bottom: 10px;"><br>
        <button id="process-btn" style="background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">
            🚀 Analyze with Puter AI
        </button>
    </div>
    <p id="status" style="color: #ffc107; margin-top: 10px;"></p>
    <pre id="output" style="background: #000; padding: 10px; font-size: 12px; max-height: 200px; overflow-y: auto; border-radius: 5px; display: none;"></pre>
</div>

<script>
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
    
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const processBtn = document.getElementById('process-btn');
    
    processBtn.onclick = async () => {
        const fileInput = document.getElementById('pdf-file');
        if (!fileInput.files.length) {
            status.innerText = "Please select a PDF first.";
            return;
        }

        status.innerText = "Initializing Puter AI...";
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = async function() {
            const typedarray = new Uint8Array(this.result);
            const pdf = await pdfjsLib.getDocument(typedarray).promise;
            let results = [];

            for (let i = 1; i <= pdf.numPages; i++) {
                status.innerText = `AI is looking at page ${i} of ${pdf.numPages}...`;
                
                // Convert PDF Page to Image
                const page = await pdf.getPage(i);
                const viewport = page.getViewport({scale: 1.5});
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                await page.render({canvasContext: context, viewport: viewport}).promise;
                
                const base64Image = canvas.toDataURL('image/jpeg', 0.8);

                // Call Puter AI Vision
                try {
                    const response = await puter.ai.chat(
                        "Return ONLY a JSON object for this debris ticket: {\\"date\\":\\"MM/DD/YYYY\\", \\"id\\":\\"ticket_number\\", \\"type\\":\\"HANGER/LEANER\\", \\"measure\\": 0.0}",
                        base64Image
                    );
                    
                    const cleanJson = response.message.content.replace(/```json|```/g, "").trim();
                    results.push(JSON.parse(cleanJson));
                } catch (err) {
                    console.error("AI Page Error:", err);
                }
            }

            // Send data back to Streamlit or handle it here
            status.innerText = "✅ Analysis Complete!";
            output.style.display = "block";
            output.innerText = JSON.stringify(results, null, 2);
            
            // Trigger a custom event to notify Streamlit if needed
            // For now, we will handle CSV generation directly in the browser for speed
            generateCSV(results);
        };
        reader.readAsArrayBuffer(file);
    };

    function generateCSV(data) {
        let csv = "Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\\nProject Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\\nDate,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\\n";
        
        data.forEach(item => {
            let row = Array(19).fill(" $- ");
            row[0] = item.date; row[1] = item.id; row[2] = "848117"; row[3] = "Fernando";
            row[11] = ""; row[12] = "";

            let m = parseFloat(item.measure) || 0;
            if (item.type.toUpperCase().includes("HANGER")) {
                row[4] = "1";
                row[5] = " $35.00 "; row[10] = " $35.00 "; row[13] = " $40.00 "; row[18] = " $40.00 ";
            } else {
                row[4] = m;
                if (m > 0 && m <= 23.99) { row[6] = " $80.00 "; row[10] = " $80.00 "; row[14] = " $100.00 "; row[18] = " $100.00 "; }
                else if (m >= 24 && m <= 35.99) { row[7] = " $150.00 "; row[10] = " $150.00 "; row[15] = " $175.00 "; row[18] = " $175.00 "; }
                else if (m >= 36 && m <= 47.99) { row[8] = " $175.00 "; row[10] = " $175.00 "; row[16] = " $200.00 "; row[18] = " $200.00 "; }
                else if (m >= 48) { row[9] = " $250.00 "; row[10] = " $250.00 "; row[17] = " $275.00 "; row[18] = " $275.00 "; }
            }
            csv += row.join(",") + "\\n";
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'MasterLog_Output.csv';
        a.click();
    }
</script>
"""

# 2. Render the component in Streamlit
components.html(puter_component, height=600, scrolling=True)

st.markdown("""
---
### How it works:
1. **Local Processing:** The PDF is rendered in your browser. 
2. **Puter AI:** The images are sent to Puter's multimodal AI model (no API key required in code).
3. **CSV Export:** The range sorting logic ($80, $150, etc.) is calculated instantly and the CSV is downloaded directly to your computer.
""")
