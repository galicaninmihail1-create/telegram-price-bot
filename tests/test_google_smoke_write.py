from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.services.google_sheets import GoogleSheetsError
from app.services.google_smoke_write import (
    GoogleSmokeWriteService,
    SmokeImageError,
    SmokeSheetsWriteError,
)


@pytest.mark.asyncio
async def test_writes_exactly_one_file_and_one_test_row(tmp_path: Path) -> None:
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"fake-jpeg")
    drive = AsyncMock()
    sheets = AsyncMock()
    drive.upload.return_value = ("file-id", "https://drive.invalid/file-id")

    product = await GoogleSmokeWriteService(drive, sheets).run(image)

    drive.upload.assert_awaited_once()
    sheets.append.assert_awaited_once_with(product)
    assert product.telegram_message_id == "SMOKE_TEST"
    assert product.category == "TEST PRODUCT"
    assert str(product.price_rub) == "1000"
    assert str(product.rub_byn_rate) == "0.035"
    assert str(product.base_price_byn) == "35"
    assert str(product.final_price_byn) == "35"
    assert product.status == "TEST"
    assert drive.upload.await_args.args[1].startswith("smoke-test-")
    assert drive.upload.await_args.args[1].endswith(".jpg")
    assert drive.upload.await_args.args[2] == "image/jpeg"


@pytest.mark.asyncio
async def test_png_keeps_extension(tmp_path: Path) -> None:
    image = tmp_path / "photo.PNG"
    image.write_bytes(b"fake-png")
    drive = AsyncMock()
    sheets = AsyncMock()
    drive.upload.return_value = ("file-id", "url")

    await GoogleSmokeWriteService(drive, sheets).run(image)

    assert drive.upload.await_args.args[1].endswith(".png")
    assert drive.upload.await_args.args[2] == "image/png"


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["missing.jpg", "photo.gif"])
async def test_rejects_invalid_image_before_api_calls(tmp_path: Path, filename: str) -> None:
    image = tmp_path / filename
    if image.suffix == ".gif":
        image.write_bytes(b"fake-gif")
    drive = AsyncMock()
    sheets = AsyncMock()

    with pytest.raises(SmokeImageError):
        await GoogleSmokeWriteService(drive, sheets).run(image)

    drive.upload.assert_not_awaited()
    sheets.append.assert_not_awaited()


@pytest.mark.asyncio
async def test_reports_partial_failure_without_deleting_drive_file(tmp_path: Path) -> None:
    image = tmp_path / "photo.jpeg"
    image.write_bytes(b"fake-jpeg")
    drive = AsyncMock()
    sheets = AsyncMock()
    drive.upload.return_value = ("kept-file-id", "https://drive.invalid/kept-file-id")
    sheets.append.side_effect = GoogleSheetsError("offline fake error")

    with pytest.raises(SmokeSheetsWriteError) as error:
        await GoogleSmokeWriteService(drive, sheets).run(image)

    assert error.value.drive_file_id == "kept-file-id"
    assert error.value.drive_url == "https://drive.invalid/kept-file-id"
    drive.upload.assert_awaited_once()
    sheets.append.assert_awaited_once()
