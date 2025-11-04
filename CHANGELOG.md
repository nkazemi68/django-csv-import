## v0.3.0 (2025-11-04)

### Feat

- **project**: add django admin settings and related configs like static and staticfiles in settings and compose, plus a fake large csv creator script

## v0.2.4 (2025-11-03)

### Fix

- **apps**: fix importer ImportTask object creation problem in upload view

## v0.2.3 (2025-11-03)

### Fix

- **api**: fix importer app task status endpoint url

## v0.2.2 (2025-11-03)

### Fix

- **apps**: fix importer app test methods and urls names

## v0.2.1 (2025-11-03)

### Fix

- **api**: fix importer background tasks status update to success even if all
  csv rows has problems, means it's a successfull try

## v0.2.0 (2025-11-03)

### Feat

- **apps**: add ImportService and related utils, Celery task and between usages,
  to import books from csv
- **api**: add DRF serializers, views and urls for import endpoints
- **apps**: add importer app and related Book and ImportTask models and its
  configs
- **project**: add drf spectacular for swagger support and its settings, plus
  media root and gzip middleware
- **project**: add django project skeleton and requirements
