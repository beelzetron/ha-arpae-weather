from datetime import date, datetime
import importlib.util
from pathlib import Path
import sys

API_PATH = Path(__file__).parents[1] / "custom_components" / "arpae_weather" / "api.py"
SPEC = importlib.util.spec_from_file_location("arpae_weather_api", API_PATH)
assert SPEC and SPEC.loader
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)

build_daily_forecast = api.build_daily_forecast
current_condition = api.current_condition
parse_bulletin = api.parse_bulletin
parse_forecast_number = api.parse_forecast_number
parse_weather_alert = api.parse_weather_alert


def make_bulletin():
    bollettino = {
        "tipo": "previsione",
        "emissione": "02/06/2026",
        "validita": "oggi, martedi 2 giugno 2026",
        "regionale": {
            "testo": {
                "cielo": "Sereno",
                "temperatura": "Stabili",
                "venti": "Deboli",
            },
        },
        "dati": {
            "temperatura_minima": {
                "1": {"descrizione": "BOLOGNA (BO)", "dato": "11"},
                "2": {"descrizione": "MODENA (MO)", "dato": "13"},
            },
            "temperatura_massima": {
                "1": {"descrizione": "BOLOGNA (BO)", "dato": "22"},
                "2": {"descrizione": "MODENA (MO)", "dato": "25"},
            },
        },
        "provinciale": {
            "MO": {
                "descrizione": "Modena",
                "mattina": {
                    "P": {"icona": "a001", "it": "sereno", "en": "clear"},
                    "C": {"icona": "a005", "it": "nuvoloso", "en": "cloudy"},
                    "R": {"icona": "a006", "it": "pioggia", "en": "rain"},
                },
                "pomeriggio": {
                    "P": {"icona": "a002", "it": "poco nuvoloso", "en": "partly cloudy"},
                },
                "sera_notte": {
                    "P": {"icona": "b001", "it": "sereno", "en": "clear"},
                },
                "dati_tabellari": {
                    "pianura": {
                        "tmin_previ": "10",
                        "tmax_previ": "21",
                        "precipitazioni": "0",
                        "vento_massimo": "15",
                    },
                    "collina": {
                        "tmin_previ": "8",
                        "tmax_previ": "19",
                        "precipitazioni": "2",
                        "vento_massimo": "22",
                    },
                    "rilievi": {
                        "tmin_previ": "4",
                        "tmax_previ": "15",
                        "precipitazioni": "5",
                        "vento_massimo": "30",
                    },
                },
                "testo_previsione": "Testo",
            },
        },
    }
    return {
        "oggi": {"bollettino": bollettino},
        "domani": {"bollettino": bollettino},
        "dopodomani": {"bollettino": bollettino},
    }


def test_parse_bulletin_uses_configured_province_temperatures():
    day = parse_bulletin(make_bulletin(), "MO", "P")[0]

    assert day.tmin == "13"
    assert day.tmax == "25"
    assert day.slots[0].condition == "Sereno"
    assert day.slots[0].icon == "sunny"


def test_parse_bulletin_uses_hill_zone_table_fallback():
    bulletin = make_bulletin()
    bollettino = bulletin["oggi"]["bollettino"]
    bollettino["dati"]["temperatura_minima"] = None
    bollettino["dati"]["temperatura_massima"] = None

    day = parse_bulletin(bulletin, "MO", "C")[0]

    assert day.tmin == "8"
    assert day.tmax == "19"
    assert day.precipitation == "2"
    assert day.wind == "22"


def test_build_daily_forecast_maps_arpae_days_to_weather_forecasts():
    forecasts = tuple(parse_bulletin(make_bulletin(), "MO", "P"))

    daily = build_daily_forecast(forecasts, date(2026, 6, 2))

    assert daily[0] == {
        "datetime": "2026-06-02T00:00:00+00:00",
        "condition": "sunny",
        "native_temperature": 25.0,
        "native_templow": 13.0,
        "native_precipitation": 0.0,
        "native_wind_speed": 15.0,
    }
    assert daily[1]["datetime"] == "2026-06-03T00:00:00+00:00"
    assert daily[2]["datetime"] == "2026-06-04T00:00:00+00:00"


def test_current_condition_uses_today_slot_for_local_time():
    forecasts = tuple(parse_bulletin(make_bulletin(), "MO", "P"))

    assert current_condition(forecasts, datetime(2026, 6, 2, 9)) == "sunny"
    assert current_condition(forecasts, datetime(2026, 6, 2, 15)) == "partlycloudy"
    assert current_condition(forecasts, datetime(2026, 6, 2, 21)) == "clear-night"


def test_parse_forecast_number_extracts_first_decimal_value():
    assert parse_forecast_number("12,5 mm") == 12.5
    assert parse_forecast_number("-2 / 3") == -2.0
    assert parse_forecast_number("assenti") is None
    assert parse_forecast_number(None) is None


def test_parse_weather_alert_returns_none_without_active_alerts():
    alert = parse_weather_alert(
        {
            "titolo": "Bollettino di vigilanza",
            "C2": {
                "idraulica": "green",
                "idrogeologica": "green",
                "temporali": None,
                "vento": "green",
            },
        },
        "C2",
    )

    assert alert is None


def test_parse_weather_alert_extracts_active_phenomena_and_max_severity():
    alert = parse_weather_alert(
        {
            "titolo": "Allerta 054/2026 valida dalle 00:00 del 02/06/2026: vento, temporali",
            "link": "/documents/20181/4392413/allerta054_2026.pdf",
            "dataInizio": "Jun 2, 2026 12:00:00 AM",
            "dataFine": "Jun 3, 2026 12:00:00 AM",
            "descrizionemeteo": "Sono previsti vento e temporali.",
            "C2": {
                "idraulica": "green",
                "idrogeologica": "green",
                "temporali": "yellow",
                "vento": "orange",
                "neve": None,
            },
        },
        "c2",
    )

    assert alert is not None
    assert alert.zone == "C2"
    assert alert.color == "orange"
    assert alert.link == "https://allertameteo.regione.emilia-romagna.it/documents/20181/4392413/allerta054_2026.pdf"
    assert [(item.key, item.label, item.color) for item in alert.phenomena] == [
        ("temporali", "Temporali", "yellow"),
        ("vento", "Vento", "orange"),
    ]
