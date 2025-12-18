import time
from PyPDF2 import PdfReader
from rich import print as pprint

pdf_path = "QualityGPInformation_F1_3F_Layout.pdf"

start_time = time.time()

reader = PdfReader(pdf_path)

all_text = ""

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f"--- Page {i + 1} ---")
    print(text)
    print()

    all_text += f"\n--- Page {i+1} ---\n{text}\n"

end_time = time.time()

pprint(all_text)

elapsed = end_time - start_time
pprint(f"Elapsed time: {elapsed:.2f} seconds")