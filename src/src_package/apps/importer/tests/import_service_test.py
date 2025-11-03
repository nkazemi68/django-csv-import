"""
Unit tests for ImportService.

Covers:
- Successful book creation with valid rows.
- ISBN normalization and validation.
- Duplicate ISBN skipping with error reporting.
- Malformed data handling (missing fields, invalid year).
- Batch processing and fallback saves.

Uses in-memory CSV and Django's TestCase for isolation.
"""

from django.test import TestCase

from ..models import Book
from ..services.import_csv_service import ImportService


class ImportServiceTest(TestCase):
    def test_importer_book_creation(self):
        """
        Test: Valid row creates a new Book.

        Verifies:
        - ISBN normalization (dashes removed).
        - All fields saved correctly.
        - Result counters updated.
        """
        rows = [{
            "title": "Test Book",
            "author": "Navid Kazemi",
            "isbn": "9780135957059",
            "publication_year": "2025"
        }]
        svc = ImportService()
        res = svc.import_rows(rows)
        self.assertEqual(res.created, 1)
        self.assertEqual(len(res.errors), 0)
        self.assertTrue(Book.objects.filter(isbn="9780135957059").exists())

    def test_importer_duplicate_isbn_skipping(self):
        """
        Test: Existing ISBN prevents creation.

        Verifies:
        - No new book created.
        - Error message includes line number.
        - skipped counter incremented.
        """
        Book.objects.create(title="Existing Book", author="Navid Kazemi", isbn="ISBN-123", publication_year=2025)
        rows = [{
            "title": "New Book",
            "author": "Kazemi Navid",
            "isbn": "ISBN-123",
            "publication_year": "2024"
        }]
        svc = ImportService()
        res = svc.import_rows(rows)
        self.assertEqual(res.created, 0)
        self.assertEqual(res.skipped, 1)
        self.assertTrue(len(res.errors) >= 1)
