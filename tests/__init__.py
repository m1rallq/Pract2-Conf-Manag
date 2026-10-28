"""Тесты проекта. Добавляет папку src в путь импорта."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
