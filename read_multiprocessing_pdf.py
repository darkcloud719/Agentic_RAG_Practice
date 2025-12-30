import multiprocessing
import time 
from PyPDF2 import PdfReader
from rich import print as pprint

PDF_TIMEOUT_SECONDS = 300
pdf_path = "test123.pdf"

def extract_pdf_text(pdf_path:str, return_dict):
    try:
        reader = PdfReader(pdf_path)
        all_text = ""

        for i, page in enumerate(reader.pages):
            all_text += f"\n--- Page {i+1} ---\n{page.extract_text()}\n"
        return_dict["text"] = all_text
    except Exception as ex:
        return_dict["error"] = str(ex)

def extract_pdf_with_timeout(pdf_path, timeout=PDF_TIMEOUT_SECONDS):
    
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=extract_pdf_text, args=(pdf_path, return_dict))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return "timeout"
    
    if "error" in return_dict:
        pprint(f"⚠ Error during PDF extraction: {return_dict['error']}")
        return None
    
    return return_dict.get("text", None)

def main():

    start_time = time.time()
    result = extract_pdf_with_timeout(pdf_path, PDF_TIMEOUT_SECONDS)
    elapsed = time.time() - start_time

    if result is None:
        pprint("❌ PDF processing failed due to error.")
    elif result == "timeout":
        pprint(f"⏱ PDF processing skipping due to timeout ({PDF_TIMEOUT_SECONDS}) seconds.")
    else:
        pprint(result)

    pprint(f"Elapsed time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()