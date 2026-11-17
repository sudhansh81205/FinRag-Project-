"""Explicitly recover the official pinned E/F/G cross-encoder; runtime stays offline."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.retrieval.cross_encoder import ASSETS, MODEL, REVISION, verify_assets  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / "output/models-reranker")
    parser.add_argument("--download", action="store_true", help="Explicitly download missing official assets; approximately1.14GB")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.download:
        for name in ASSETS:
            path = args.directory / name
            if path.exists():
                continue  # verification below rejects stale bytes; never silently overwrite
            temporary = path.with_suffix(path.suffix + ".download")
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "2",
                            "--connect-timeout", "15", "--max-time", "1200", "--output", str(temporary),
                            f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}"], check=True)
            temporary.rename(path)
            print("Recovered official asset:", name, flush=True)
    manifest = verify_assets(args.directory)
    (args.directory / "verified-assets.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "verified", "model": MODEL, "revision": REVISION,
                      "directory": str(args.directory), "acceptance": "candidate assets; independent gate remains separate"}))


if __name__ == "__main__":
    main()
