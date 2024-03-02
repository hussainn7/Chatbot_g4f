import tkinter as tk
from tkinter import messagebox
import requests


class WeatherAirPollutionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather and Air Pollution Data")
        self.geometry("400x400")

        self.api_key = "b9cd298593ba9f5db898d737ff3107bd"

        self.create_widgets()

    def create_widgets(self):
        self.city_label = tk.Label(self, text="Enter City Name:")
        self.city_label.pack(pady=(20, 5))

        self.city_entry = tk.Entry(self)
        self.city_entry.pack(pady=(0, 20))

        self.weather_button = tk.Button(self, text="Get Weather", command=self.get_weather)
        self.weather_button.pack()

        self.air_pollution_button = tk.Button(self, text="Get Air Pollution for Bishkek",
                                              command=self.get_air_pollution)
        self.air_pollution_button.pack(pady=20)

        self.result_text = tk.Text(self, height=10, width=50)
        self.result_text.pack(pady=(20, 0))

    def get_weather(self):
        city_name = self.city_entry.get()
        if not city_name:
            messagebox.showerror("Error", "Please enter a city name")
            return
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={self.api_key}'
        response = requests.get(weather_url)
        weather_info = response.json()

        if weather_info['cod'] == 200:
            kelvin = 273
            temp = int(weather_info['main']['temp'] - kelvin)
            feels_like_temp = int(weather_info['main']['feels_like'] - kelvin)
            humidity = weather_info['main']['humidity']
            description = weather_info['weather'][0]['description']

            weather = (f"Weather of: {city_name}\n"
                       f"Temperature (Celsius): {temp}°\n"
                       f"Feels like (Celsius): {feels_like_temp}°\n"
                       f"Humidity: {humidity}%\n"
                       f"Description: {description.capitalize()}")
        else:
            weather = f"Weather for '{city_name}' not found! Please enter a valid city name."
        self.display_result(weather)

    def get_air_pollution(self):
        lat = 42.8746
        lon = 74.5698
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={self.api_key}"
        response = requests.get(url)
        data = response.json()
        self.display_air_pollution_data(data)

    def display_air_pollution_data(self, data):
        if data.get("list"):
            pollution_data = data["list"][0]
            aqi = pollution_data["main"]["aqi"]
            pm25_concentration = pollution_data["components"]["pm2_5"]
            us_aqi_pm25 = self.calculate_aqi_pm25(pm25_concentration)

            result = (f"OpenWeatherMap AQI: {aqi} (1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor)\n"
                      f"Estimated US AQI for PM2.5: {us_aqi_pm25}\n"
                      "Pollutant concentrations (µg/m3):\n")
            for pollutant, value in pollution_data["components"].items():
                result += f"  {pollutant.upper()}: {value}\n"
        else:
            result = "No air pollution data available."
        self.display_result(result)

    def calculate_aqi_pm25(self, concentration):
        # Your AQI calculation logic here
        # Simplified for brevity; please insert your original function
        return round(concentration * 9)  # Placeholder calculation

    def display_result(self, text):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)


if __name__ == "__main__":
    app = WeatherAirPollutionApp()
    app.mainloop()
