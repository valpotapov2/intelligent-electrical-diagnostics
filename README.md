# Intelligent Electrical Diagnostics

Проект интеллектуальной диагностики электрооборудования. Основной пользовательский принцип: электрик загружает электрическую схему; система автоматически извлекает сведения, строит частичную модель и задаёт только необходимые уточняющие вопросы.

## OCR ingestion MVP

Первый исполняемый прототип находится в `src/edi_ingest`.

### Возможности

- PDF и растровые изображения;
- OCR через Tesseract;
- сохранение распознанных токенов, координат и confidence;
- поиск обозначений QF, KM, TA, шин L1/L2/L3/N/PE и АВР;
- создание чернового JSON с provenance.

**Важно:** текущий MVP пока не распознаёт графические символы и не восстанавливает электрические соединения. Он не должен называться готовым парсером электрических схем.

### Установка

Нужен установленный Tesseract OCR и языковые данные для русского и английского языков.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Пример для Debian/Ubuntu:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### Запуск

```bash
edi-ingest path/to/diagram.pdf --object-name "Kindergarten switchboard" -o model.draft.json --ocr-output ocr.json
```

Для изображения:

```bash
edi-ingest path/to/diagram.png --lang rus+eng -o model.draft.json
```

### Тесты

```bash
pytest
```

См. [статус MVP](docs/architecture/ingestion-mvp-status.md), [конвейер обработки схем](docs/architecture/diagram-ingestion-pipeline.md) и [формат графовой модели](docs/architecture/electrical-object-graph.md).
