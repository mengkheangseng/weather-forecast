from flask import Flask, jsonify, request
import urllib.request
import urllib.parse
import json

def fetch_json(url, headers={}):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())
    
def geocode(city):
    params = urllib.parse.urlencode({
        "q": city,
        "format": "json",
        "limit": 1,
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    data = fetch_json(url, headers={"User-Agent": "WeatherCLI/1.0"})

    if not data:
        raise ValueError(f"City not found: '{city}'")

    result = data[0]
    return float(result["lat"]), float(result["lon"]), result["display_name"]

WMO_CODES = {
    0:  "Clear sky",
    1:  "Mainly clear",   2: "Partly cloudy",  3: "Overcast",
    45: "Foggy",          48: "Icy fog",
    51: "Light drizzle",  53: "Drizzle",        55: "Heavy drizzle",
    61: "Light rain",     63: "Rain",           65: "Heavy rain",
    71: "Light snow",     73: "Snow",           75: "Heavy snow",
    80: "Light showers",  81: "Showers",        82: "Heavy showers",
    95: "Thunderstorm",   99: "Heavy thunderstorm",
}

SLOT_HOURS = {
    "Morning 6am":  6,
    "Noon 12pm":   12,
    "Evening 6pm": 18,
}

def get_forecast(lat, lon):
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,weathercode,windspeed_10m,precipitation_probability",
        "temperature_unit": "celsius",
        "windspeed_unit": "kmh",
        "forecast_days": 3,
        "timezone": "auto",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    return fetch_json(url)



app = Flask(__name__)

@app.route("/weather")
def weather():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "No city provided"}), 400

    try:
        lat, lon, display_name = geocode(city)
        forecast = get_forecast(lat, lon)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Something went wrong"}), 500

    from datetime import date, timedelta
    today = date.today()
    days = [
        ("Today",               today),
        ("Tomorrow",            today + timedelta(days=1)),
        ("Day after tomorrow",  today + timedelta(days=2)),
    ]

    times = forecast["hourly"]["time"]
    temps = forecast["hourly"]["temperature_2m"]
    codes = forecast["hourly"]["weathercode"]
    winds = forecast["hourly"]["windspeed_10m"]
    probs = forecast["hourly"]["precipitation_probability"]

    by_time = {
        t: {"temp": temps[i], "code": codes[i], "wind": winds[i], "prob": probs[i]}
        for i, t in enumerate(times)
    }

    result = {"city": display_name, "days": []}

    for day_label, day_date in days:
        slots = []
        for slot_name, hour in SLOT_HOURS.items():
            key = f"{day_date}T{hour:02d}:00"
            if key in by_time:
                d = by_time[key]
                slots.append({
                    "slot": slot_name,
                    "weather": WMO_CODES.get(d["code"], "Unknown"),
                    "temp": d["temp"],
                    "wind": d["wind"],
                    "rain": d["prob"],
                })
        result["days"].append({
            "label": day_label,
            "date": str(day_date),
            "slots": slots,
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)