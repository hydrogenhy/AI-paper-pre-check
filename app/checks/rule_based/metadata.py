
from PyPDF2 import PdfReader

def extract_metadata(pdf_path):
    high_resk = ["/Author", "/Creator", "/Producer"]
    mid_resk = ["/Title", "/Subject", "/Keywords"]
    low_resk = ["/CreationDate", "/ModDate", "/PTEX.Fullbanner", "/Trapped"]
    order = {"high": 0, "medium": 1, "low": 2, "unknown": 3,}

    if pdf_path[-4:].lower() != ".pdf":
        return {
            "check_type": "metadata",
            "results": "NOT a PDF file"
        }

    reader = PdfReader(pdf_path)
    metadata = reader.metadata

    if metadata is None:
        return {
            "check_type": "metadata",
            "results": "no metadata found"
            }

    details = {
        "check_type": "metadata",
        "results": sorted(
            [
                {
                    key: metadata[key],
                    "confidence": (
                        "high" if key in high_resk
                        else "medium" if key in mid_resk
                        else "low" if key in low_resk
                        else "unknown"
                    ),
                }
                for key in metadata.keys()
            ],
            key=lambda x: order.get(x["confidence"], 99),
        ),
    }

    return details