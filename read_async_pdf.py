import asyncio
import time
from PyPDF2 import PdfReader
from rich import print as pprint

PDF_TIMEOUT_SECONDS = 30
pdf_path = "QualityGPInformation_F1_3F_Layout.pdf"

def extract_pdf_text_sync(pad_path:str) -> str:
    
    reader = PdfReader(pdf_path)
    all_text = ""

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        all_text += f"\n--- Page {i+1} ---\n{text}\n"

    return all_text

async def extract_pdf_text_async(pdf_path:str) -> str:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(extract_pdf_text_sync, pdf_path),
            timeout=PDF_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        pprint("⚠ PDF extraction exceeded time limit. Bypassing.")
        return None
    
async def main():
    start_time = time.time()

    result = await extract_pdf_text_async(pdf_path)

    elapsed = time.time() - start_time
    
    if result is None:
        pprint("❌ PDF processing skipped due to timeout.")
    else:
        pprint(result)

    pprint(f"Elapsed time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())