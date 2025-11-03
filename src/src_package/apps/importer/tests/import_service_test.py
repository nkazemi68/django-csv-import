from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..services.import_csv_service import ImportService, ImportResult
from ..models import Book, ImportTask
import io, csv


class ImportServiceTest(TestCase):
    def test_importer_book_creation(self):
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
