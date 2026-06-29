from pathlib import Path


def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def get_document_title(content: str, fallback_title: str) -> str:
    for line in content.splitlines():
        cleaned_line = line.strip()

        if cleaned_line.startswith("# "):
            return cleaned_line.replace("# ", "", 1).strip()

    return fallback_title


def split_markdown_into_chunks(content: str, max_chars: int = 300) -> list[str]:
    paragraphs: list[str] = []
    current_paragraph: list[str] = []

    for line in content.splitlines():
        cleaned_line = line.strip()

        if cleaned_line == "":
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
        else:
            current_paragraph.append(cleaned_line)

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    chunks: list[str] = []
    current_chunk = ""

    for paragraph in paragraphs:
        if not current_chunk:
            current_chunk = paragraph
        elif len(current_chunk) + len(paragraph) + 2 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{paragraph}"
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def load_and_chunk_support_documents(
    documents_dir: Path,
    max_chars: int = 300,
) -> list[dict]:
    all_chunks: list[dict] = []

    for file_path in sorted(documents_dir.glob("*.md")):
        content = read_markdown_file(file_path)
        title = get_document_title(content, fallback_title=file_path.stem)

        chunks = split_markdown_into_chunks(
            content=content,
            max_chars=max_chars,
        )

        for index, chunk_content in enumerate(chunks):
            all_chunks.append(
                {
                    "document_id": file_path.stem,
                    "title": title,
                    "content": chunk_content,
                    "source": file_path.name,
                    "chunk_index": index,
                }
            )

    return all_chunks