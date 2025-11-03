"""
Service layer for importing book data from CSV rows.

This module handles validation, normalization, duplicate checking,
and bulk insertion of book records. It uses a repository pattern
for testability and falls back to individual saves on bulk failures.

Key features:
- ISBN normalization and validation.
- Batch processing with configurable size.
- Detailed error reporting per row.
- Atomic transactions for data integrity.
"""

import csv
from typing import List, Dict
from django.db import transaction
from ..models import Book
from .isbn_util import normalize_isbn, is_valid_isbn


class ImportResult:
    """Container for import operation outcomes.

    Attributes:
        created (int): Number of successfully created books.
        skipped (int): Number of rows skipped (e.g., duplicates).
        errors (List[Dict]): List of error details with line numbers.
    """
    def __init__(self):
        """Initialize counters and error list."""
        self.created = 0
        self.skipped = 0
        self.errors = []


def validate_row(row: Dict[str, str]):
    """Validate a single CSV row and normalize ISBN.

    Args:
        row (Dict[str, str]): Raw row data from CSV.

    Returns:
        Tuple[bool, str, str | None]:
            - bool: True if row is valid.
            - str: Error message if invalid, empty if valid.
            - str | None: Normalized ISBN or None.
    """
    raw_isbn = row.get("isbn", "")
    isbn = normalize_isbn(raw_isbn)
    title = row.get("title", "")

    if not isbn:
        return False, "missing isbn", None

    if not title:
        return False, "missing title", None

    if not is_valid_isbn(isbn):
        return False, "invalid isbn format", isbn

    return True, "", isbn


class ImportService:
    """Orchestrates the import of book rows into the database.

    Supports batch processing, duplicate detection via ISBN,
    and graceful error handling with per-row feedback.

    Attributes:
        BATCH_SIZE (int): Number of records to insert per bulk operation.
        repo: QuerySet-like interface for Book model (default: Book.objects).
    """
    BATCH_SIZE = 500  # Tune based on DB performance and memory

    def __init__(self, repo=None):
        """Initialize with optional repository for dependency injection.

        Args:
            repo: Custom repository (e.g., mock for tests).
        """
        self.repo = repo or Book.objects

    def import_rows(self, rows: List[Dict[str, str]]) -> ImportResult:
        """Process a list of CSV rows and import valid books.

        Steps:
        1. Validate and normalize all rows.
        2. Check for existing ISBNs in DB.
        3. Batch create new books with fallbacks.

        Args:
            rows (List[Dict[str, str]]): List of row dictionaries.

        Returns:
            ImportResult: Summary of created, skipped, and errors.
        """
        result = ImportResult()

        # Phase 1: Validate rows and collect normalized ISBNs
        isbns = []
        row_map = []  # Stores (row, normalized_isbn, is_valid, error_msg)
        for r in rows:
            ok, msg, normalized_isbn = validate_row(r)
            row_map.append((r, normalized_isbn, ok, msg))
            if normalized_isbn:
                isbns.append(normalized_isbn)

        # Phase 2: Bulk check for existing ISBNs
        existing = set(self.repo.filter(isbn__in=isbns).values_list("isbn", flat=True))

        # Phase 3: Prepare books for creation in batches
        books_to_create = []

        for lineno_offset, (row, normed_isbn, ok, msg) in enumerate(row_map, start=0):
            line_num = row.get("_lineno") or None  # Optional: preserve original line number

            if not ok:
                result.errors.append({"line": line_num, "message": msg})
                continue

            if normed_isbn in existing:
                result.errors.append({"line": line_num, "message": "isbn already exists"})
                result.skipped += 1
                continue

            # Parse publication year safely
            try:
                pub_year = int(row.get("publication_year")) if row.get("publication_year") else None
            except Exception:
                result.errors.append({"line": line_num, "message": "invalid publication_year"})
                continue

            # Build Book instance with normalized ISBN
            created_book = Book(
                title=row.get("title"),
                author=row.get("author") or "",
                isbn=normed_isbn,
                publication_year=pub_year
            )
            books_to_create.append(created_book)

            # Flush batch when full
            if len(books_to_create) >= self.BATCH_SIZE:
                self._bulk_save(books_to_create, result)
                # Update known existing ISBNs to avoid re-querying
                existing.update([book.isbn for book in books_to_create])
                books_to_create = []

        # Final batch
        if books_to_create:
            self._bulk_save(books_to_create, result)

        return result

    def _bulk_save(self, objs, result: ImportResult):
        """Save a batch of books with bulk_create and per-object fallback.

        Args:
            objs: Books to save.
            result (ImportResult): Mutable result object to update.
        """
        try:
            with transaction.atomic():
                self.repo.bulk_create(objs)

            result.created += len(objs)
        except Exception as exc:
            # Log bulk failure and fall back to individual saves
            # Useful for unique constraint violations not caught earlier
            for o in objs:
                try:
                    with transaction.atomic():
                        o.save()
                        result.created += 1
                except Exception as e:
                    result.errors.append({"line": "unknown", "message": str(e)})
