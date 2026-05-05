import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from WebApp.services.booking_service import calculate_total_price

def test_calculate_total_price_basic():
    """Alap számítás tesztelése: 2 éjszaka, normál ár, nincs per-person szorzó."""
    # 1. Mockoljuk a Room objektumot! Így NEM kell adatbázis rekordot létrehozni.
    mock_room = Mock()
    mock_room.price_per_night = 10000.0

    check_in = datetime(2026, 6, 1)
    check_out = datetime(2026, 6, 3) # 2 éjszaka

    # 2. Függvény meghívása
    total = calculate_total_price(
        room=mock_room,
        check_in=check_in,
        check_out=check_out
    )

    # 3. Ellenőrzés: 2 * 10000 = 20000
    assert total == 20000.0

def test_calculate_total_price_per_person():
    """Fejenkénti árképzés tesztelése több vendég esetén."""
    mock_room = Mock()
    mock_room.price_per_night = 10000.0

    check_in = datetime(2026, 6, 1)
    check_out = datetime(2026, 6, 4) # 3 éjszaka

    total = calculate_total_price(
        room=mock_room,
        check_in=check_in,
        check_out=check_out,
        guests_count=2,
        price_per_person=True
    )

    # Ellenőrzés: 3 éjszaka * 10000 * 2 fő = 60000
    assert total == 60000.0

def test_calculate_total_price_with_extras_and_same_day():
    """Azonos napi kijelentkezés (minimum 1 éjszaka) és extrák tesztelése."""
    mock_room = Mock()
    mock_room.price_per_night = 15000.0

    check_in = datetime(2026, 6, 1)
    check_out = datetime(2026, 6, 1) # 0 nap különbség, de a függvény max(1, ...) alapján számol

    total = calculate_total_price(
        room=mock_room,
        check_in=check_in,
        check_out=check_out,
        extras=5000.0
    )

    # Ellenőrzés: (1 éjszaka * 15000) + 5000 extra = 20000
    assert total == 20000.0