from pathlib import Path

import click
import frontmatter
import httpx
from tqdm import tqdm


def find_markdowns(source_dir: Path) -> list[Path]:
    return list(source_dir.rglob("*.md"))


def parse_document(path: Path, base_dir: Path) -> tuple[str, str]:
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    rel_path = path.relative_to(base_dir).with_suffix("")
    document = post.metadata.get("document", str(rel_path))
    return document, post.content


@click.command()
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--indexer-url", required=True, help="Indexer API URL")
def upload(source_dir: Path, indexer_url: str):
    md_files = find_markdowns(source_dir)
    if not md_files:
        click.echo(f"No markdown files found in {source_dir}")
        return

    click.echo(f"Found {len(md_files)} documents to upload")

    items = []
    for md_file in md_files:
        document, text = parse_document(md_file, source_dir)
        items.append({"text": text, "document": document})

    batches = [items[i : i + 100] for i in range(0, len(items), 100)]
    client = httpx.Client(timeout=300)
    total_chunks = 0
    for batch in tqdm(batches, desc="Uploading batches"):
        try:
            response = client.post(
                f"{indexer_url}/documents",
                json={"items": batch},
            )
        except httpx.TimeoutException:
            click.echo("Request timed out. Is the indexer server running?")
            return
        except httpx.ConnectError:
            click.echo(f"Could not connect to {indexer_url}. Is the server running?")
            return

        if response.status_code >= 400:
            click.echo(f"Error: {response.status_code} - {response.text}")
            return

        response.raise_for_status()
        result = response.json()
        total_chunks += result["chunks_created"]

    click.echo(f"Done. Total chunks: {total_chunks}")


if __name__ == "__main__":
    upload()
