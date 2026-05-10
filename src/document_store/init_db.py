import json
import sys
from pathlib import Path

from tqdm import tqdm

from .main import get_table


def read_all_chunks(data_dir: str) -> list[dict[str, str]]:
    result = []
    base_path = Path(data_dir)

    if not base_path.exists():
        raise Exception("directory not found")

    chunks_files = base_path.glob("*/chunks.json")

    for chunks_file in chunks_files:
        document_name = chunks_file.parent.name

        try:
            with chunks_file.open("r", encoding="utf-8") as f:
                chunks_data = json.load(f)

            if isinstance(chunks_data, list):
                for chunk_text in chunks_data:
                    if isinstance(chunk_text, str):
                        result.append({"document": document_name, "text": chunk_text})
        except Exception as e:
            print(f"Error reading {chunks_file}: {e}")

    return result


def init_db(data_dir: str, batch_size: int = 1000):
    chunks = read_all_chunks(data_dir)
    print(f"Loaded {len(chunks)} chunks from {data_dir}")

    table = get_table()

    for i in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i : i + batch_size]
        table.add(batch)

    table.create_fts_index("text", replace=True)
    print("FTS index created successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init_db.py <data_dir>")
        sys.exit(1)

    init_db(sys.argv[1])
