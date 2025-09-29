import time
import requests
import pandas as pd

API_URL = "https://archive-api.open-meteo.com/v1/archive?"

COORDINATES = {
    "madrid": {"latitude": 40.416775, "longitude": -3.703790},
    "london": {"latitude": 51.507351, "longitude": -0.127758},
    "rio": {"latitude": -22.906847, "longitude": -43.172896},
}

VARIABLES = ["temperature_2m_mean", "precipitation_sum", "wind_speed_10m_max"]


# Función auxiliar genérica para llamadar a APIs
def call_api(url: str, params: dict, retries: int = 3, backoff: int = 5):
    """
    Llamar a una API con gestión de errores y rate limit.
    - retries: número de intentos en caso de error temporal
    - backoff: segundos de espera entre intentos (cool off)
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)

            # Caso 429: Rate limit alcanzado
            if response.status_code == 429:
                print(f"[{attempt}] Rate limit alcanzado. Esperando {backoff} segundos...")
                time.sleep(backoff)
                continue

            # Otros errores HTTP
            if response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                return None

            # Respuesta OK
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[{attempt}] Error en la llamada a la API: {e}")
            time.sleep(backoff)

    print("Error persistente: no se pudo obtener respuesta de la API")
    return None


# Función que llama a la API de Open-Meteo
def get_data_meteo_api(city: str, start_date: str, end_date: str):
    if city not in COORDINATES:
        raise ValueError(f"La ciudad {city} no está en la lista de coordinates")

    lat = COORDINATES[city]["latitude"]
    lon = COORDINATES[city]["longitude"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(VARIABLES),
        "timezone": "auto",
    }

    data = call_api(API_URL, params=params)

    if not data or "daily" not in data:
        print(f"No se recibieron datos válidos para {city}")
        return pd.DataFrame()

    # Pasar los datos diarios a DataFrame
    df = pd.DataFrame(data["daily"])
    df["city"] = city  # Añadir ciudad como columna
    return df

#Agrupo los datos por trimestres para luego poder representarlos
def agrupacion_trimestral(df):
 if df.empty:
     return pd.DataFrame()
 
#convierto la columna time a tipo datatime
 df["time"]=pd.to_datetime(df["time"])
 #agrupo por meses y calculo la media de cada mes
 df["year_month"]=df["time"].dt.to_period("Q") #Q agrupa por trimenstres
 df_mensual=df.groupby(["city","year_month"])[VARIABLES].mean().reset_index()
 return df_mensual



#Creo los gráficos

import  matplotlib.pyplot as plt

def grafico(df_mensual):
    if df_mensual.empty:
        print("No hay datos para graficar")
        return
    
    for var in VARIABLES:
        plt.figure(figsize=(5,30))
        for ciudad in df_mensual["city"].unique():
            df_ciudad =df_mensual[df_mensual["city"]==ciudad]
            plt.plot(df_ciudad["year_month"].astype(str),df_ciudad[var],label=ciudad)

        plt.xticks(rotation=45)
        plt.xlabel("Trimestre")
        plt.ylabel(var)
        plt.title(f"Evolución trimestral de {var}")
        plt.legend()
        plt.tight_layout()
        plt.show()




#función principal

def main():
    ciudades = ["madrid", "london", "rio"]
    inicio = "2010-01-01"
    fin = "2020-12-31"

    todos_datos = pd.DataFrame()
    #Obtener los datos diarios de todas las ciudades
    for ciudad in ciudades:
        df_ciudad = get_data_meteo_api(ciudad, inicio, fin)
        todos_datos = pd.concat([todos_datos, df_ciudad], ignore_index=True)

    print(todos_datos.head(20))
    
    #Agrupar por mes y calcular medias 
    df_mensual = agrupacion_trimestral(todos_datos)

    #graficar la evolución tempora
    grafico(df_mensual)



if __name__ == "__main__":
    main()





