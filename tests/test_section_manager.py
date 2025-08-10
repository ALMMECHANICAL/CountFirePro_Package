import os
import sys
import pytest

# Ensure the project root is on the Python path so section_manager can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from section_manager import SectionManager


def make_section(x, y, width, height):
    return {"coordinates": {"x": x, "y": y, "width": width, "height": height}}


def test_validate_section_valid():
    manager = SectionManager()
    section = make_section(10, 10, 20, 20)
    assert manager.validate_section(section, (100, 100)) is True


def test_validate_section_non_positive_size():
    manager = SectionManager()
    invalid_sections = [
        make_section(0, 0, 0, 10),   # zero width
        make_section(0, 0, 10, 0),   # zero height
        make_section(0, 0, -5, 10),  # negative width
        make_section(0, 0, 10, -5),  # negative height
    ]
    for section in invalid_sections:
        assert manager.validate_section(section, (100, 100)) is False


def test_validate_section_exceeds_boundaries():
    manager = SectionManager()
    image_shape = (100, 100)
    invalid_sections = [
        make_section(90, 90, 20, 20),  # extends beyond bottom-right
        make_section(100, 0, 10, 10),  # x starts outside image
        make_section(0, 100, 10, 10),  # y starts outside image
        make_section(95, 0, 10, 10),   # width causes overflow
        make_section(0, 95, 10, 10),   # height causes overflow
    ]
    for section in invalid_sections:
        assert manager.validate_section(section, image_shape) is False
