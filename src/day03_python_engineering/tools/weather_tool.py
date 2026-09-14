import httpx

from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city: str = Field(
        min_length=1,
        max_length=100,
        description="城市名称",
    )

async def get_weather(city: str, *, client: httpx.AsyncClient) -> str:
    location_response = await client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "zh"},
    )
    location_response.raise_for_status()
    locations = location_response.json().get("results", [])
    if not locations:
        raise ValueError(f"未找到城市：{city}")

    location = locations[0]
    weather_response = await client.get(
        "https://api.open-meteo.com/v1/forecast",
            
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m",
        },
    )
    weather_response.raise_for_status()
    #temperature = weather_response.json()["current"]

    return f"{location['name']}当前气温 {weather_response.text}°C。"
