import csv
from typing import List, Dict
from django.db import transaction
from ..models import Book
from .isbn_util import normalize_isbn, is_valid_isbn


class ImportResult:
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.errors = []


def validate_row(row: Dict[str, str]):
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
    BATCH_SIZE = 500

    def __init__(self, repo=None):
        self.repo = repo or Book.objects

    def import_rows(self, rows: List[Dict[str, str]]) -> ImportResult:
        result = ImportResult()
        # book isbns will be collected from normalized rows
        isbns = []
        row_map = []
        for r in rows:
            ok, msg, normalized_isbn = validate_row(r)
            row_map.append((r, normalized_isbn, ok, msg))
            if normalized_isbn:
                isbns.append(normalized_isbn)

        existing = set(self.repo.filter(isbn__in=isbns).values_list("isbn", flat=True))
        books_to_create = []

        for lineno_offset, (row, normed_isbn, ok, msg) in enumerate(row_map, start=0):
            # get real line number if exists
            line_num = row.get("_lineno") or None
            if not ok:
                result.errors.append({"line": line_num, "message": msg})
                continue
            if normed_isbn in existing:
                result.errors.append({"line": line_num, "message": "isbn already exists"})
                result.skipped += 1
                continue
            # create Book instance but set isbn = normalized
            try:
                pub_year = int(row.get("publication_year")) if row.get("publication_year") else None
            except Exception:
                result.errors.append({"line": line_num, "message": "invalid publication_year"})
                continue

            created_book = Book(
                title=row.get("title"),
                author=row.get("author") or "",
                isbn=normed_isbn,
                publication_year=pub_year
            )
            books_to_create.append(created_book)

            if len(books_to_create) >= self.BATCH_SIZE:
                self._bulk_save(books_to_create, result)
                # refresh existing set
                existing.update([book.isbn for book in books_to_create])
                books_to_create = []
        if books_to_create:
            self._bulk_save(books_to_create, result)

        return result

    def _bulk_save(self, objs, result: ImportResult):
        try:
            with transaction.atomic():
                self.repo.bulk_create(objs)

            result.created += len(objs)
        except Exception as exc:
            # fallback: save one by one
            for o in objs:
                try:
                    with transaction.atomic():
                        o.save()
                        result.created += 1
                except Exception as e:
                    result.errors.append({"line": "unknown", "message": str(e)})
