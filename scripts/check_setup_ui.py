"""Exercise the actual running Gradio endpoint without a model or paid API call.

Start `python app.py` first, then run `python scripts/check_setup_ui.py`.
"""

import argparse
import json
import urllib.request

from gradio_client import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:7860")
    args = parser.parse_args()
    with urllib.request.urlopen(args.url, timeout=20) as response:
        assert response.status == 200
        assert "FinRAG" in response.read().decode("utf-8")
    client = Client(args.url, verbose=False)
    result = client.predict("What is Apple's revenue?", api_name="/check_readiness")
    assert result[0] == "not_ready", result[0]
    assert result[2] == "", "Setup UI must not fabricate a financial answer."
    assert result[3] == [], "Setup UI must not fabricate source evidence."
    empty = client.predict("  ", api_name="/check_readiness")
    assert empty[0] == "invalid_input", empty[0]
    assert empty[2] == ""
    print(json.dumps({"http_status": 200, "question_status": result[0],
                      "empty_question_status": empty[0], "answer_empty": True,
                      "evidence_empty": True, "real_model_called": False}, indent=2))


if __name__ == "__main__":
    main()
