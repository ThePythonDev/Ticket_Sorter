import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Glyphon", layout="wide")

# HEADER
st.title("Glyphon Ticket Proccesser")

st.info("""
Only one or two poeple should be using the app at a time due to Streamlit limits.  
Process scanned tickets via Puter.js AI.  
Please take note that accuracy is 97%  
(Double checking tickets is recommended for complete accuracy)  
Please contact Soren Clink at sorenclink@gmail.com if any errors occur
""")

st.markdown("""
### Instructions:
1. Select your PDF file in the box above.
2. Click **Start AI Analysis**.
3. Wait for the success message.
4. Click the blue **Download CSV spreadsheet** button to save your file.
""")

st.divider()

puter_component = """
<div style="background:#0e1117;padding:25px;border-radius:12px;border:1px solid #30363d;color:white;font-family:sans-serif">

<script src="https://js.puter.com/v2/"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>

<div style="text-align:center;padding:35px;border:2px dashed #444;border-radius:10px;background:#161b22">
<input type="file" id="pdf-file" accept="application/pdf" style="margin-bottom:15px"><br>

<button id="process-btn" style="
background:#238636;
padding:14px 26px;
border-radius:8px;
border:none;
color:white;
font-weight:bold;
cursor:pointer;
font-size:16px">
Start AI Analysis
</button>
</div>

<p id="status" style="margin-top:15px;color:#e3b341;font-weight:bold"></p>
<progress id="progress-bar" value="0" max="100" style="width:100%; height:20px; display:none; margin-top:10px;"></progress>

<div id="download-container" style="display:none;margin-top:20px;padding:20px;background:#21262d;border-radius:8px;text-align:center">
<p style="color:#7ee787">✅ Analysis Complete!</p>
<button id="download-csv-btn" style="
background:#1f6feb;
border:none;
padding:12px 22px;
border-radius:6px;
color:white;
font-weight:bold;
cursor:pointer">
Download CSV spreadsheet
</button>
</div>

<details style="margin-top:20px">
<summary style="color:#8b949e">View Raw AI Data (JSON)</summary>
<pre id="output" style="background:black;padding:15px;border-radius:6px;margin-top:10px;max-height:250px;overflow:auto"></pre>
</details>

</div>

<script>
pdfjsLib.GlobalWorkerOptions.workerSrc =
'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

const status = document.getElementById("status");
const progressBar = document.getElementById("progress-bar");
const output = document.getElementById("output");
const btn = document.getElementById("process-btn");
const download = document.getElementById("download-container");
const downloadBtn = document.getElementById("download-csv-btn");

let processedData = [];

async function processPage(pageNum, pdf) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({scale: 1.0});
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await page.render({canvasContext: ctx, viewport: viewport}).promise;
    const img = canvas.toDataURL("image/jpeg", 0.7);

    const text = await puter.ai.img2txt({source: img, provider:"mistral"});

    const response = await puter.ai.chat(
        "Extract debris ticket info. Return ONLY JSON {date:'MM/DD/YYYY', id:'number', type:'HANGER/LEANER', measure:0.0}",
        text
    );
    const clean = response.message.content.replace(/```json|```/g,"").trim();
    return JSON.parse(clean);
}

btn.onclick = async () => {
    const file = document.getElementById("pdf-file").files[0];
    if (!file) {
        status.innerText = "❌ Please select a PDF file first.";
        return;
    }

    btn.disabled = true;
    download.style.display = "none";
    processedData = [];
    progressBar.style.display = "block";
    progressBar.value = 0;

    const reader = new FileReader();
    reader.onload = async function() {
        const pdf = await pdfjsLib.getDocument(new Uint8Array(this.result)).promise;
        status.innerText = `AI is analyzing ${pdf.numPages} pages...`;

        const totalPages = pdf.numPages;
        const pagePromises = [];

        for (let i = 1; i <= totalPages; i++) {
            pagePromises.push(
                processPage(i, pdf).then(result => {
                    processedData.push(result);
                    progressBar.value = (processedData.length / totalPages) * 100;
                })
            );
        }

        await Promise.all(pagePromises);

        status.innerText = "";
        output.innerText = JSON.stringify(processedData, null, 2);
        download.style.display = "block";
        btn.disabled = false;
        progressBar.style.display = "none";
    };
    reader.readAsArrayBuffer(file);
};

downloadBtn.onclick = () => {
    let csv = "Contractor:,LUVKIN,,,,,,,,,,,,,,,,,\\nProject Name:,PRENTISS CO L/H,,,,,,,,,,,,,,,,,\\nDate,Ticket,Truck ID,Driver Name,1= HANGER / LEANER DIAMETER,$35.00,$80.00,$150.00,$175.00,$250.00,Sub Total,,, $40.00 ,$100.00,$175.00,$200.00,$275.00,TLM Total\\n";

    processedData.forEach(item => {
        let row = Array(19).fill(" $- ");
        row[0] = item.date || "";
        row[1] = item.id || "";
        row[2] = "848117";
        row[3] = "Fernando";
        row[11] = "";
        row[12] = "";

        let m = parseFloat(item.measure) || 0;
        let type = (item.type || "").toUpperCase();

        if (type.includes("HANGER")) {
            row[4] = "1";
            row[5] = " $35.00 ";
            row[10] = " $35.00 ";
            row[13] = " $40.00 ";
            row[18] = " $40.00 ";
        } else {
            row[4] = m.toString();
            if (m > 0 && m <= 23.99) { row[6]=" $80.00 "; row[10]=" $80.00 "; row[14]=" $100.00 "; row[18]=" $100.00 "; }
            else if (m >= 24 && m <= 35.99) { row[7]=" $150.00 "; row[10]=" $150.00 "; row[15]=" $175.00 "; row[18]=" $175.00 "; }
            else if (m >= 36 && m <= 47.99) { row[8]=" $175.00 "; row[10]=" $175.00 "; row[16]=" $200.00 "; row[18]=" $200.00 "; }
            else if (m >= 48) { row[9]=" $250.00 "; row[10]=" $250.00 "; row[17]=" $275.00 "; row[18]=" $275.00 "; }
        }
        csv += row.join(",")+"\\n";
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "_generated.csv";
    link.click();
};
</script>
"""

components.html(puter_component, height=850)

st.divider()
st.write("© Copyright Soren Clink 2026 all rights reserved")
