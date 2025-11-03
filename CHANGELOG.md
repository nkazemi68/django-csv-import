## v0.2.1 (2025-11-03)

### Fix

- **api**: fix importer background tasks status update to success even if all csv rows has problems, means its a successfull try

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
