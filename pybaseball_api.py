"""
API REST con FastAPI para funciones de pybaseball.
Documentación: http://localhost:8000/docs (Swagger UI)
Alternativa: http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import pybaseball as pyb
import pandas as pd
import json
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================
app = FastAPI(
    title="PyBaseball API",
    description="API REST para acceder a datos de béisbol (MLB) usando pybaseball",
    version="1.0.0",
    contact={
        "name": "Claudio - Agente n8n",
        "email": "fabian.mestre@gmail.com",
    }
)

# Habilitar CORS para que otros servicios puedan consumir la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELOS PYDANTIC (para validar requests/responses)
# ============================================================================

class BattingStatsRequest(BaseModel):
    """Parámetros para obtener estadísticas de bateo"""
    start_season: int = Field(..., description="Primera temporada (ej: 2020)")
    end_season: Optional[int] = Field(None, description="Última temporada (opcional)")
    league: str = Field("all", description="Liga: 'all', 'nl', 'al', 'mnl'")
    qual: Optional[int] = Field(None, description="Mínimo de plate appearances")
    ind: int = Field(1, description="1=por temporada, 0=agregado")


class PitchingStatsRequest(BaseModel):
    """Parámetros para obtener estadísticas de pitcheo"""
    start_season: int = Field(..., description="Primera temporada")
    end_season: Optional[int] = Field(None, description="Última temporada (opcional)")
    league: str = Field("all", description="Liga: 'all', 'nl', 'al', 'mnl'")
    qual: Optional[int] = Field(None, description="Mínimo de innings")
    ind: int = Field(1, description="1=por temporada, 0=agregado")


class StatcastRequest(BaseModel):
    """Parámetros para obtener datos de Statcast"""
    start_dt: str = Field(..., description="Fecha inicio (YYYY-MM-DD)")
    end_dt: Optional[str] = Field(None, description="Fecha fin (YYYY-MM-DD, opcional)")
    team: Optional[str] = Field(None, description="Equipo (ej: NYY, BOS)")


class PlayerIdRequest(BaseModel):
    """Parámetros para buscar ID de jugador"""
    last: str = Field(..., description="Apellido del jugador")
    first: Optional[str] = Field(None, description="Nombre del jugador")
    fuzzy: bool = Field(False, description="Búsqueda aproximada")


class DataframeResponse(BaseModel):
    """Respuesta genérica con datos en formato JSON"""
    success: bool = Field(True, description="Indica si la operación fue exitosa")
    data: List[dict] = Field(..., description="Datos en formato JSON")
    count: int = Field(..., description="Número de filas retornadas")
    timestamp: str = Field(..., description="Timestamp de la respuesta")


class RankingRecord(BaseModel):
    """Record individual del ranking"""
    rank: int
    player_name: str
    value: float
    percentile: Optional[float] = None


class RankingResponse(BaseModel):
    """Respuesta de un ranking"""
    ranking_id: str
    ranking_name: str
    metric: str
    description: str
    top_10: List[RankingRecord]
    league_avg: Optional[float] = None
    league_min: Optional[float] = None
    league_max: Optional[float] = None
    timestamp: str

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

def dataframe_to_response(df: pd.DataFrame) -> dict:
    """
    Convierte un DataFrame de pandas a formato JSON para la respuesta.

    Args:
        df: DataFrame a convertir

    Returns:
        dict con estructura de respuesta
    """
    try:
        data = json.loads(df.to_json(orient='records'))
        return {
            "success": True,
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar datos: {str(e)}")


# ============================================================================
# RUTAS - ESTADÍSTICAS DE BATEO
# ============================================================================

@app.post("/batting-stats", response_model=DataframeResponse, tags=["Bateo"])
async def get_batting_stats(request: BattingStatsRequest):
    """
    Obtiene estadísticas de bateo del sitio FanGraphs.

    **Ejemplo:**
    ```
    {
        "start_season": 2020,
        "end_season": 2023,
        "league": "all",
        "qual": 100,
        "ind": 1
    }
    ```
    """
    try:
        df = pyb.batting_stats(
            start_season=request.start_season,
            end_season=request.end_season,
            league=request.league,
            qual=request.qual,
            ind=request.ind
        )
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/batting-stats-bref/{season}", tags=["Bateo"])
async def get_batting_stats_bref(season: int):
    """
    Obtiene estadísticas de bateo de Baseball Reference para una temporada.
    Solo disponible desde 2008.

    **Parámetro:**
    - season: Año (ej: 2023)
    """
    try:
        df = pyb.batting_stats_bref(season)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/batting-stats-range", tags=["Bateo"])
async def get_batting_stats_range(
    start_dt: str = Query(..., description="YYYY-MM-DD"),
    end_dt: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    """
    Obtiene estadísticas de bateo en un rango de fechas de Baseball Reference.

    **Parámetros:**
    - start_dt: Fecha inicio (YYYY-MM-DD)
    - end_dt: Fecha fin (YYYY-MM-DD, opcional)
    """
    try:
        df = pyb.batting_stats_range(start_dt, end_dt)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - ESTADÍSTICAS DE PITCHEO
# ============================================================================

@app.post("/pitching-stats", response_model=DataframeResponse, tags=["Pitcheo"])
async def get_pitching_stats(request: PitchingStatsRequest):
    """
    Obtiene estadísticas de pitcheo de FanGraphs.

    **Ejemplo:**
    ```
    {
        "start_season": 2020,
        "end_season": 2023,
        "league": "all",
        "ind": 1
    }
    ```
    """
    try:
        df = pyb.pitching_stats(
            start_season=request.start_season,
            end_season=request.end_season,
            league=request.league,
            qual=request.qual,
            ind=request.ind
        )
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pitching-stats-bref/{season}", tags=["Pitcheo"])
async def get_pitching_stats_bref(season: int):
    """
    Obtiene estadísticas de pitcheo de Baseball Reference para una temporada.
    Solo disponible desde 2008.
    """
    try:
        df = pyb.pitching_stats_bref(season)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pitching-stats-range", tags=["Pitcheo"])
async def get_pitching_stats_range(
    start_dt: str = Query(..., description="YYYY-MM-DD"),
    end_dt: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    """
    Obtiene estadísticas de pitcheo en un rango de fechas.
    """
    try:
        df = pyb.pitching_stats_range(start_dt, end_dt)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - STATCAST (datos de pitch-by-pitch)
# ============================================================================

@app.post("/statcast", response_model=DataframeResponse, tags=["Statcast"])
async def get_statcast(request: StatcastRequest):
    """
    Obtiene datos de Statcast (pitch-by-pitch) para un rango de fechas.

    Datos disponibles desde 2008.

    **Ejemplo:**
    ```
    {
        "start_dt": "2023-04-01",
        "end_dt": "2023-04-30",
        "team": "NYY"
    }
    ```
    """
    try:
        df = pyb.statcast(
            start_dt=request.start_dt,
            end_dt=request.end_dt,
            team=request.team
        )
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/statcast-batter/{player_id}", tags=["Statcast"])
async def get_statcast_batter(
    player_id: int,
    start_dt: str = Query(..., description="YYYY-MM-DD"),
    end_dt: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    """
    Obtiene datos de Statcast para un bateador específico.

    **Parámetros:**
    - player_id: ID del jugador (MLBAM)
    - start_dt: Fecha inicio
    - end_dt: Fecha fin (opcional)
    """
    try:
        df = pyb.statcast_batter(start_dt, end_dt, player_id)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/statcast-pitcher/{player_id}", tags=["Statcast"])
async def get_statcast_pitcher(
    player_id: int,
    start_dt: str = Query(..., description="YYYY-MM-DD"),
    end_dt: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    """
    Obtiene datos de Statcast para un lanzador específico.
    """
    try:
        df = pyb.statcast_pitcher(start_dt, end_dt, player_id)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - BÚSQUEDA DE JUGADORES
# ============================================================================

@app.post("/player-lookup", tags=["Jugadores"])
async def player_lookup(request: PlayerIdRequest):
    """
    Busca IDs de un jugador por nombre (MLBAM, FanGraphs, Baseball Reference, Retrosheet).

    **Ejemplo:**
    ```
    {
        "last": "Trout",
        "first": "Mike",
        "fuzzy": false
    }
    ```
    """
    try:
        df = pyb.playerid_lookup(request.last, request.first, request.fuzzy)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/player-reverse-lookup/{player_ids}", tags=["Jugadores"])
async def player_reverse_lookup(
    player_ids: str = Path(..., description="IDs separados por comas"),
    key_type: str = Query("mlbam", description="Tipo: mlbam, retro, bbref, fangraphs")
):
    """
    Busca nombre del jugador dado su ID.

    **Parámetros:**
    - player_ids: IDs separados por comas (ej: 116539,116541,641728)
    - key_type: Tipo de ID (mlbam, retro, bbref, fangraphs)
    """
    try:
        ids = [int(x.strip()) for x in player_ids.split(",")]
        df = pyb.playerid_reverse_lookup(ids, key_type)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




# ============================================================================
# RUTA RAÍZ
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """
    Endpoint raíz con información de la API.
    """
    return {
        "title": "PyBaseball API REST",
        "version": "1.0.0",
        "description": "API para acceder a datos de béisbol MLB",
        "docs_url": "/docs (Swagger UI)",
        "redoc_url": "/redoc (ReDoc)",
        "endpoints": {
            "bateo": "/batting-stats, /batting-stats-bref/{season}",
            "pitcheo": "/pitching-stats, /pitching-stats-bref/{season}",
            "statcast": "/statcast, /statcast-batter/{player_id}",
            "jugadores": "/player-lookup, /player-reverse-lookup",
            "equipos": "/team-batting, /team-pitching",
            "war": "/war-batting, /war-pitching",
            "otros": "/standings/{season}, /splits/{playerid}"
        }
    }




# ============================================================================
# CONFIGURACIÓN Y FUNCIONES PARA RANKINGS (GOOGLE SHEETS)
# ============================================================================

import gspread
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_SHEET_ID = "1O9vFxcntbHRa5EUGL-b3yyMwICc2GNSdvwYPLEaTPro"



# ============================================================================
# ENDPOINTS - RANKINGS (29 RANKINGS DESDE GOOGLE SHEETS)
# ============================================================================

@app.get("/rankings", tags=["Rankings"])
async def list_rankings():
    """Lista todos los rankings disponibles"""
    rankings = {"1": "Exit Velocity", "2": "Expected Stats", "3": "Home Runs", "4": "Percentiles", "5": "Batting Run Value", "6": "Swing Path", "7": "Bat Tracking", "8": "Batting Stance", "9": "Batted Ball", "10": "Pitch Arsenal Stats", "11": "Pitch Tempo", "12": "cat-Catcher Framing", "13": "cat-Pop Time", "14": "cat-Catcher Blocking", "15": "cat-Catcher Stance", "16": "cat-Catcher Throwing", "17": "run-Sprint Speed", "18": "run-Baserunning Run Value", "19": "run-Basestealing Run Value", "20": "run-Extra Bases Taken", "21": "run-90ft Running Splits", "22": "fld-Fielding Run Value", "23": "fld-Arm Strength", "24": "fld-Arm Value", "25": "fld-Outfield Catch Prob", "26": "fld-Outfield Dir OAA", "27": "fld-Outfielder Jump", "28": "fld-Outs Above Average", "29": "Year to Year Changes"}
    return {"available_rankings": rankings, "total": 29, "usage": "GET /rankings/{ranking_id}"}


@app.get("/rankings/1", response_model=RankingResponse, tags=["Rankings"])
async def get_ranking_1():
    """Obtiene el ranking 1 (Exit Velocity)"""
    try:
        sheet_name = "Exit Velocity"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        new_cols = ['player', 'player_id', 'attempts', 'avg_hit_angle', 'angle_sweet_spot', 'max_hit_speed', 'avg_hit_speed', 'ev50', 'fbld', 'gb', 'max_distance', 'avg_distance']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols
        metric = "avg_hit_speed"
        df_clean = df.dropna(subset=[metric])
        df_sorted = df_clean.sort_values(metric, ascending=False)
        df_top = df_sorted.head(10)
        top_10 = []
        for idx, (_, row) in enumerate(df_top.iterrows(), 1):
            pct = (df_clean[metric] <= row[metric]).sum() / len(df_clean) * 100
            name = str(row['player'])
            top_10.append(RankingRecord(rank=idx, player_name=name, value=round(float(row[metric]), 2), percentile=round(pct, 1)))
        return RankingResponse(ranking_id="1", ranking_name="Exit Velocity Promedio", metric="avg_hit_speed", description="Velocidad promedio de los golpes en mph. Mide la potencia general del bateador.", top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_exit_velocity_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Exit Velocity"""
    try:
        sheet_name = "Exit Velocity"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        new_cols = ['player', 'player_id', 'attempts', 'avg_hit_angle', 'angle_sweet_spot', 'max_hit_speed', 'avg_hit_speed', 'ev50', 'fbld', 'gb', 'max_distance', 'avg_distance', 'avg_hr_distance', 'ev95plus', 'ev95percent', 'barrels', 'brl_percent', 'brl_pa', 'unnamed']
        df.columns = new_cols
        df_clean = df.dropna(subset=[metric])
        df_sorted = df_clean.sort_values(metric, ascending=ascending)
        df_top = df_sorted.head(10)
        top_10 = []
        for idx, (_, row) in enumerate(df_top.iterrows(), 1):
            pct = (df_clean[metric] <= row[metric]).sum() / len(df_clean) * 100 if not ascending else (df_clean[metric] >= row[metric]).sum() / len(df_clean) * 100
            name = str(row['player'])
            top_10.append(RankingRecord(rank=idx, player_name=name, value=round(float(row[metric]), 2), percentile=round(pct, 1)))
        return RankingResponse(ranking_id=metric, ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rankings/exit-speed-max", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_exit_speed_max():
    """Top 10 por velocidad máxima de golpe"""
    return generate_exit_velocity_ranking("max_hit_speed", "Velocidad Máxima de Golpe", "Velocidad máxima registrada del golpe en mph. Indica el pico de potencia del bateador.")


@app.get("/rankings/hit-distance-avg", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_hit_distance_avg():
    """Top 10 por distancia promedio de golpes"""
    return generate_exit_velocity_ranking("avg_distance", "Distancia Promedio de Golpes", "Distancia promedio en pies que viajan los golpes. Mide la capacidad de mandar lejos la bola.")


@app.get("/rankings/hit-distance-max", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_hit_distance_max():
    """Top 10 por distancia máxima de golpe"""
    return generate_exit_velocity_ranking("max_distance", "Distancia Máxima de Golpe", "Golpe más lejano registrado en pies. Muestra el potencial máximo del bateador.")


@app.get("/rankings/barrels", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_barrels():
    """Top 10 por cantidad de barrels"""
    return generate_exit_velocity_ranking("barrels", "Cantidad de Barrels", "Cantidad de 'barrels' (golpes óptimos según MLB). Un barrel es un contacto óptimo que resulta en alta probabilidad de éxito.")


@app.get("/rankings/sweet-spot", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_sweet_spot():
    """Top 10 por porcentaje de golpes en sweet spot"""
    return generate_exit_velocity_ranking("angle_sweet_spot", "% Golpes en Zona Óptima", "Porcentaje de golpes que hacen contacto en la zona óptima del bate. Mide consistencia y control.")


@app.get("/rankings/power-consistency", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_power_consistency():
    """Top 10 por porcentaje de golpes con potencia (>95 mph)"""
    return generate_exit_velocity_ranking("ev95percent", "% Golpes con Potencia (>95mph)", "Porcentaje de golpes con exit velocity mayor a 95 mph. Mide consistencia de potencia.")


@app.get("/rankings/ev-median", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_ev_median():
    """Top 10 por exit velocity mediana"""
    return generate_exit_velocity_ranking("ev50", "Exit Velocity Mediana (EV50)", "Exit velocity en el percentil 50 de todos los golpes. Mide el valor medio de potencia.")


@app.get("/rankings/power-threshold-count", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_power_threshold_count():
    """Top 10 por cantidad de golpes > 95 mph"""
    return generate_exit_velocity_ranking("ev95plus", "Golpes con Potencia (>95mph)", "Cantidad total de golpes con exit velocity superior a 95 mph. Mide frecuencia de potencia.")


@app.get("/rankings/homerun-distance-avg", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_homerun_distance_avg():
    """Top 10 por distancia promedio de home runs"""
    return generate_exit_velocity_ranking("avg_hr_distance", "Distancia Promedio Home Runs", "Distancia promedio en pies de los home runs bateados. Mide potencia en hits más efectivos.")


@app.get("/rankings/barrel-percentage", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_barrel_percentage():
    """Top 10 por porcentaje de barrels"""
    return generate_exit_velocity_ranking("brl_percent", "% Barrels", "Porcentaje de golpes que son barrels. Mide calidad del contacto respecto al total de golpes.")


@app.get("/rankings/barrel-pa", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_barrel_pa():
    """Top 10 por barrels por plate appearance"""
    return generate_exit_velocity_ranking("brl_pa", "Barrels por Aparición", "Promedio de barrels por plate appearance. Mide eficiencia de golpes de calidad.")


@app.get("/rankings/flyball-velocity", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_flyball_velocity():
    """Top 10 por velocidad fly ball/line drive"""
    return generate_exit_velocity_ranking("fbld", "Velocidad Fly Ball/Line Drive", "Exit velocity promedio en fly balls y line drives. Mide potencia en hits elevados.")


@app.get("/rankings/groundball-velocity", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_groundball_velocity():
    """Top 10 por velocidad ground ball"""
    return generate_exit_velocity_ranking("gb", "Velocidad Ground Ball", "Exit velocity promedio en ground balls. Mide velocidad de golpes rasantes.")


@app.get("/rankings/hit-angle", response_model=RankingResponse, tags=["Rankings - Exit Velocity"])
async def ranking_hit_angle():
    """Top 10 por ángulo promedio de golpe"""
    return generate_exit_velocity_ranking("avg_hit_angle", "Ángulo Promedio de Golpe", "Ángulo promedio en grados de los golpes. Ángulos óptimos (15-35°) favorecen distancia.")


@app.get("/debug/ranking1-raw", tags=["Debug"])
async def debug_ranking1_raw():
    """DEBUG: Returns raw first 3 rows of Exit Velocity sheet"""
    try:
        sheet_name = "Exit Velocity"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        new_cols = ['player', 'player_id', 'attempts', 'avg_hit_angle', 'angle_sweet_spot', 'max_hit_speed', 'avg_hit_speed', 'ev50', 'fbld', 'gb', 'max_distance', 'avg_distance']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols
        return {
            "columns": df.columns.tolist(),
            "first_3_rows": df[['player', 'avg_hit_speed']].head(3).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


# ============================================================================
# RUTAS - EXPECTED STATS (RANKINGS)
# ============================================================================

def generate_expected_stats_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Expected Stats"""
    try:
        sheet_name = "Expected Stats"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura real: last_name, first, player_id, year, pa, bip, ba, est_ba, est_ba_minus_b, slg, est_slg, est_slg_minus_s, woba, est_woba, est_woba_minus_woba_diff, col_o
        new_cols = ['last_name', 'first', 'player_id', 'year', 'pa', 'bip', 'ba', 'est_ba', 'est_ba_minus_b', 'slg', 'est_slg', 'est_slg_minus_s', 'woba', 'est_woba', 'est_woba_minus_woba_diff']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = f"{row['last_name']}, {row['first']}" if pd.notna(row['last_name']) and pd.notna(row['first']) else str(row.get('last_name', row.get('first', '')))
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/debug/expected-stats-raw", tags=["Debug"])
async def debug_expected_stats_raw():
    """DEBUG: Ver estructura de Expected Stats sheet"""
    try:
        sheet_name = "Expected Stats"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/rankings/expected-batting-average", response_model=RankingResponse, tags=["Rankings - Expected Stats"])
async def ranking_expected_batting_average():
    """Top 10 por xBA (Expected Batting Average)"""
    return generate_expected_stats_ranking("est_ba", "Expected Batting Average (xBA)", "Promedio de bateo esperado basado en calidad de contacto. xBA predice mejor desempeño que BA actual.")


@app.get("/rankings/expected-slugging", response_model=RankingResponse, tags=["Rankings - Expected Stats"])
async def ranking_expected_slugging():
    """Top 10 por xSLG (Expected Slugging)"""
    return generate_expected_stats_ranking("est_slg", "Expected Slugging (xSLG)", "Slugging esperado basado en bolas puestas en juego. Indicador predictivo de poder.", ascending=False)


@app.get("/rankings/expected-obp", response_model=RankingResponse, tags=["Rankings - Expected Stats"])
async def ranking_expected_obp():
    """Top 10 por xOBP (Expected On-Base Percentage)"""
    return generate_expected_stats_ranking("xobp", "Expected On-Base Percentage (xOBP)", "OBP esperado basado en calidad de contacto y disciplina.")


@app.get("/rankings/expected-woba", response_model=RankingResponse, tags=["Rankings - Expected Stats"])
async def ranking_expected_woba():
    """Top 10 por xwOBA (Expected Weighted On-Base Average)"""
    return generate_expected_stats_ranking("est_woba", "Expected wOBA (xwOBA)", "wOBA esperado basado en la calidad de los golpes. Mejor predictor que wOBA actual.")


# ============================================================================
# RUTAS - HOME RUNS (RANKINGS)
# ============================================================================

@app.get("/debug/home-runs-raw", tags=["Debug"])
async def debug_home_runs_raw():
    """DEBUG: Ver estructura de Home Runs sheet"""
    try:
        sheet_name = "Home Runs"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def generate_home_runs_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Home Runs"""
    try:
        sheet_name = "Home Runs"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura real: player, player_id, team_abbrev, year, type, avg_hr_trot, doublers, mostly_gone, no_doublers, no_doubler_per_hr_total, xhr, xhr_diff
        new_cols = ['player', 'player_id', 'team_abbrev', 'year', 'type', 'avg_hr_trot', 'doublers', 'mostly_gone', 'no_doublers', 'no_doubler_per_hr_total', 'xhr', 'xhr_diff']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row['player'])
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rankings/home-run-trot-time", response_model=RankingResponse, tags=["Rankings - Home Runs"])
async def ranking_home_run_trot_time():
    """Top 10 por tiempo promedio de trote en home runs"""
    return generate_home_runs_ranking("avg_hr_trot", "Tiempo Promedio de Trote en HR", "Tiempo promedio (en segundos) del trote en home runs. Jugadores más rápidos tienen menores tiempos.", ascending=True)


@app.get("/rankings/home-run-doublers", response_model=RankingResponse, tags=["Rankings - Home Runs"])
async def ranking_home_run_doublers():
    """Top 10 por cantidad de home runs doublers"""
    return generate_home_runs_ranking("doublers", "Home Runs Doublers", "Cantidad de home runs clasificados como 'doublers' (bolas que podrían caer como dobles). Mide HRs más cercanos a la línea de foul.")


@app.get("/rankings/home-run-mostly-gone", response_model=RankingResponse, tags=["Rankings - Home Runs"])
async def ranking_home_run_mostly_gone():
    """Top 10 por home runs mostly gone"""
    return generate_home_runs_ranking("mostly_gone", "Home Runs Mostly Gone", "Cantidad de home runs clasificados como 'mostly gone' (claramente fuera). HRs con trayectoria más definitiva.")


@app.get("/rankings/expected-home-runs", response_model=RankingResponse, tags=["Rankings - Home Runs"])
async def ranking_expected_home_runs():
    """Top 10 por home runs esperados (xHR)"""
    return generate_home_runs_ranking("xhr", "Expected Home Runs (xHR)", "Cantidad esperada de home runs basada en calidad de contacto. xHR predice mejor que HR actual.")


@app.get("/rankings/home-run-efficiency", response_model=RankingResponse, tags=["Rankings - Home Runs"])
async def ranking_home_run_efficiency():
    """Top 10 por diferencia entre home runs actual vs esperado"""
    return generate_home_runs_ranking("xhr_diff", "Home Run Efficiency (HR vs xHR)", "Diferencia entre home runs actual y esperado. Positivo = bateador sobreperfoma; negativo = subperfoma.")


# ============================================================================
# RUTAS - PERCENTILES
# ============================================================================

@app.get("/debug/percentiles-raw", tags=["Debug"])
async def debug_percentiles_raw():
    """DEBUG: Ver estructura de Percentiles sheet"""
    try:
        sheet_name = "Percentiles"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def generate_percentiles_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Percentiles"""
    try:
        sheet_name = "Percentiles"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura: player_name, player_id, year, xwoba, xba, xslg, xiso, xobp, brl, brl_percent, exit_velocity, max_ev, hard_hit_percent, k_percent, bb_percent, whiff_percent, chase_percent, arm_strength, sprint_speed, oaa, bat_speed, squared_up_rate, swing_length
        new_cols = ['player_name', 'player_id', 'year', 'xwoba', 'xba', 'xslg', 'xiso', 'xobp', 'brl', 'brl_percent', 'exit_velocity', 'max_ev', 'hard_hit_percent', 'k_percent', 'bb_percent', 'whiff_percent', 'chase_percent', 'arm_strength', 'sprint_speed', 'oaa', 'bat_speed', 'squared_up_rate', 'swing_length']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row['player_name'])
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rankings/xwoba-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_xwoba_percentile():
    """Top 10 por xwOBA percentile"""
    return generate_percentiles_ranking("xwoba", "xwOBA Percentile", "Percentil de xwOBA. Mide el lugar que ocupa un bateador respecto a la liga en valor ofensivo esperado.")


@app.get("/rankings/exit-velocity-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_exit_velocity_percentile():
    """Top 10 por exit velocity percentile"""
    return generate_percentiles_ranking("exit_velocity", "Exit Velocity Percentile", "Percentil de velocidad de salida. Jugadores en altos percentiles poseen más potencia bruta.")


@app.get("/rankings/hard-hit-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_hard_hit_percentile():
    """Top 10 por hard hit percent percentile"""
    return generate_percentiles_ranking("hard_hit_percent", "Hard Hit % Percentile", "Percentil de porcentaje de golpes duros (exit velocity > 95 mph). Indica consistencia de potencia.")


@app.get("/rankings/sprint-speed-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_sprint_speed_percentile():
    """Top 10 por sprint speed percentile"""
    return generate_percentiles_ranking("sprint_speed", "Sprint Speed Percentile", "Percentil de velocidad de carrera. Atletas con altos percentiles tienen mejor velocidad base.")


@app.get("/rankings/arm-strength-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_arm_strength_percentile():
    """Top 10 por arm strength percentile"""
    return generate_percentiles_ranking("arm_strength", "Arm Strength Percentile", "Percentil de fuerza de brazo. Importante para defensores en la parte externa del campo.")


@app.get("/rankings/bat-speed-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_bat_speed_percentile():
    """Top 10 por bat speed percentile"""
    return generate_percentiles_ranking("bat_speed", "Bat Speed Percentile", "Percentil de velocidad del bate. Mayor velocidad correlaciona con más potencia potencial.")


@app.get("/rankings/whiff-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_whiff_percentile():
    """Top 10 por whiff percent percentile (orden ascendente)"""
    return generate_percentiles_ranking("whiff_percent", "Whiff % Percentile (Bajo es Mejor)", "Percentil de porcentaje de swings fallidos. Bajos percentiles indican mejor selectividad.", ascending=True)


@app.get("/rankings/walk-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_walk_percentile():
    """Top 10 por bb (walk) percent percentile"""
    return generate_percentiles_ranking("bb_percent", "Walk % Percentile", "Percentil de porcentaje de bases por bolas. Altos percentiles indican disciplina ofensiva.")


@app.get("/rankings/strikeout-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_strikeout_percentile():
    """Top 10 por k percent percentile (orden ascendente)"""
    return generate_percentiles_ranking("k_percent", "Strikeout % Percentile (Bajo es Mejor)", "Percentil de porcentaje de strikeouts. Bajos percentiles = mejor contacto.", ascending=True)


@app.get("/rankings/barrel-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_barrel_percentile():
    """Top 10 por barrel percentile"""
    return generate_percentiles_ranking("brl", "Barrel Percentile", "Percentil de barrels. Mide la cantidad de contactos óptimos según estándares MLB.")


@app.get("/rankings/outs-above-average-percentile", response_model=RankingResponse, tags=["Rankings - Percentiles"])
async def ranking_oaa_percentile():
    """Top 10 por OAA (Outs Above Average) percentile"""
    return generate_percentiles_ranking("oaa", "Outs Above Average Percentile", "Percentil de OAA. Mide valor defensivo comparado con promedio de su posición.")


# ============================================================================
# RUTAS - SWING PATH
# ============================================================================

@app.get("/debug/swing-path-raw", tags=["Debug"])
async def debug_swing_path_raw():
    """DEBUG: Ver estructura de Swing Path sheet"""
    try:
        sheet_name = "Swing Path"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def generate_swing_path_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Swing Path"""
    try:
        sheet_name = "Swing Path"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura: id, name, side, avg_bat_speed, swing_tilt, attack_angle, attack_direction, ideal_attack_angle, avg_intercept_y, avg_intercept_y, avg_batter_y_pc, avg_batter_x_pc, competitive_swings
        new_cols = ['id', 'name', 'side', 'avg_bat_speed', 'swing_tilt', 'attack_angle', 'attack_direction', 'ideal_attack_angle', 'avg_intercept_y', 'avg_intercept_x', 'avg_batter_y_pc', 'avg_batter_x_pc', 'competitive_swings']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row['name'])
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rankings/avg-bat-speed", response_model=RankingResponse, tags=["Rankings - Swing Path"])
async def ranking_avg_bat_speed():
    """Top 10 por velocidad promedio del bate"""
    return generate_swing_path_ranking("avg_bat_speed", "Velocidad Promedio del Bate", "Velocidad promedio del bate en mph. Mayor velocidad correlaciona con potencial ofensivo.")


@app.get("/rankings/swing-tilt", response_model=RankingResponse, tags=["Rankings - Swing Path"])
async def ranking_swing_tilt():
    """Top 10 por inclinación del swing"""
    return generate_swing_path_ranking("swing_tilt", "Inclinación del Swing", "Ángulo de inclinación del swing. Mide la orientación vertical del movimiento del bate.")


@app.get("/rankings/attack-angle", response_model=RankingResponse, tags=["Rankings - Swing Path"])
async def ranking_attack_angle():
    """Top 10 por ángulo de ataque"""
    return generate_swing_path_ranking("attack_angle", "Ángulo de Ataque", "Ángulo de ataque del bate en grados. Ángulos óptimos (15-35°) maximizan distancia.")


@app.get("/rankings/competitive-swings", response_model=RankingResponse, tags=["Rankings - Swing Path"])
async def ranking_competitive_swings():
    """Top 10 por cantidad de swings competitivos"""
    return generate_swing_path_ranking("competitive_swings", "Swings Competitivos", "Cantidad de swings competitivos. Mide disciplina y selectividad en zona de strike.")


# ============================================================================
# RUTAS - BAT TRACKING
# ============================================================================

@app.get("/debug/bat-tracking-raw", tags=["Debug"])
async def debug_bat_tracking_raw():
    """DEBUG: Ver estructura de Bat Tracking sheet"""
    try:
        sheet_name = "Bat Tracking"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def generate_bat_tracking_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Bat Tracking"""
    try:
        sheet_name = "Bat Tracking"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura
        new_cols = ['id', 'name', 'swings_competitive', 'percent_swings_competitive', 'contact', 'avg_bat_speed', 'hard_swing_rate', 'squared_up_per_bat_contact', 'squared_up_per_swing', 'blast_per_bat_contact', 'blast_per_swing', 'swing_length', 'swords', 'batter_run_value', 'whiffs', 'whiff_per_swing', 'batted_ball_events', 'batted_ball_event_per_swing']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row['name'])
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rankings/bat-speed", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_bat_speed():
    """Top 10 por velocidad promedio del bate"""
    return generate_bat_tracking_ranking("avg_bat_speed", "Velocidad Promedio del Bate", "Velocidad promedio del bate en mph durante swings. Correlaciona con poder ofensivo.")


@app.get("/rankings/hard-swing-rate", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_hard_swing_rate():
    """Top 10 por porcentaje de swings fuertes"""
    return generate_bat_tracking_ranking("hard_swing_rate", "% Swings Fuertes", "Porcentaje de swings donde el bateador aplica máximo esfuerzo. Mide agresividad.")


@app.get("/rankings/squared-up-contact", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_squared_up_contact():
    """Top 10 por porcentaje de contactos squared up"""
    return generate_bat_tracking_ranking("squared_up_per_bat_contact", "% Contactos Squared Up", "Porcentaje de contactos donde el bate está en posición óptima. Indica calidad de swing.")


@app.get("/rankings/blast-rate", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_blast_rate():
    """Top 10 por porcentaje de blasts por swing"""
    return generate_bat_tracking_ranking("blast_per_swing", "% Blasts por Swing", "Porcentaje de swings que resultan en 'blast' (contacto de máxima potencia). Mide consistencia de poder.")


@app.get("/rankings/batter-run-value", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_batter_run_value():
    """Top 10 por valor ofensivo (batter run value)"""
    return generate_bat_tracking_ranking("batter_run_value", "Batter Run Value", "Valor en carreras producidas por el bateador. Métrica agregada de contribución ofensiva.")


@app.get("/rankings/contact-rate", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_contact_rate():
    """Top 10 por porcentaje de contacto"""
    return generate_bat_tracking_ranking("contact", "% Contacto", "Porcentaje de swings que resultan en contacto. Indica selectividad y disciplina.")


@app.get("/rankings/whiff-rate", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_whiff_rate():
    """Top 10 por porcentaje de swings fallidos (orden ascendente)"""
    return generate_bat_tracking_ranking("whiff_per_swing", "% Whiffs por Swing (Bajo es Mejor)", "Porcentaje de swings fallidos. Bajos percentiles indican mejor control.", ascending=True)


@app.get("/rankings/swing-length", response_model=RankingResponse, tags=["Rankings - Bat Tracking"])
async def ranking_swing_length():
    """Top 10 por largo del swing"""
    return generate_bat_tracking_ranking("swing_length", "Largo del Swing", "Distancia recorrida por el bate durante el swing. Mide la extensión y rango del movimiento.")


# ============================================================================
# RUTAS - BATTED BALL
# ============================================================================

@app.get("/debug/batted-ball-raw", tags=["Debug"])
async def debug_batted_ball_raw():
    """DEBUG: Ver estructura de Batted Ball sheet"""
    try:
        sheet_name = "Batted Ball"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        return {
            "columns": df.columns.tolist(),
            "first_2_rows": df.head(2).to_dict(orient='records'),
            "total_rows": int(len(df)),
            "num_columns": int(len(df.columns))
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def generate_batted_ball_ranking(metric: str, ranking_name: str, description: str, ascending: bool = False):
    """Genera un ranking desde la hoja Batted Ball"""
    try:
        sheet_name = "Batted Ball"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        # Renombrar columnas según estructura: id, name, bbe, gb_rate, air_rate, fb_rate, ld_rate, pu_rate, pull_rate, straight_rate, oppo_rate, pull_gb_rate, straight_gb_rate, oppo_gb_rate, pull_air_rate, straight_air_rate, oppo_air_rate
        new_cols = ['id', 'name', 'bbe', 'gb_rate', 'air_rate', 'fb_rate', 'ld_rate', 'pu_rate', 'pull_rate', 'straight_rate', 'oppo_rate', 'pull_gb_rate', 'straight_gb_rate', 'oppo_gb_rate', 'pull_air_rate', 'straight_air_rate', 'oppo_air_rate']
        new_cols += [f'col_{i}' for i in range(len(new_cols), len(df.columns))]
        df.columns = new_cols

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row['name'])
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(ranking_id=ranking_name.replace(" ", "-"), ranking_name=ranking_name, metric=metric, description=description, top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rankings/fly-ball-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_fly_ball_rate():
    """Top 10 por porcentaje de fly balls"""
    return generate_batted_ball_ranking("fb_rate", "% Fly Balls", "Porcentaje de bolas bateadas que son fly balls. Mayor porcentaje indica tendencia a golpear elevado.")


@app.get("/rankings/ground-ball-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_ground_ball_rate():
    """Top 10 por porcentaje de ground balls"""
    return generate_batted_ball_ranking("gb_rate", "% Ground Balls", "Porcentaje de bolas bateadas que son ground balls. Mide tendencia a golpear rasante.")


@app.get("/rankings/line-drive-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_line_drive_rate():
    """Top 10 por porcentaje de line drives"""
    return generate_batted_ball_ranking("ld_rate", "% Line Drives", "Porcentaje de bolas bateadas que son line drives. Line drives son los más efectivos (altos promedios de batting).")


@app.get("/rankings/air-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_air_rate():
    """Top 10 por porcentaje de bolas aéreas"""
    return generate_batted_ball_ranking("air_rate", "% Bolas Aéreas (FB+LD)", "Porcentaje de bolas aéreas (fly balls + line drives). Mayor air rate = más potencial de extra-base hits.")


@app.get("/rankings/pull-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_pull_rate():
    """Top 10 por porcentaje de bolas al lado pull"""
    return generate_batted_ball_ranking("pull_rate", "% Pull Side", "Porcentaje de bolas bateadas al lado pull. Mide tendencia de lateralidad.")


@app.get("/rankings/opposite-field-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_opposite_field_rate():
    """Top 10 por porcentaje de bolas al campo opuesto"""
    return generate_batted_ball_ranking("oppo_rate", "% Campo Opuesto", "Porcentaje de bolas bateadas al campo opuesto. Indica versatilidad ofensiva.")


@app.get("/rankings/straight-center-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_straight_center_rate():
    """Top 10 por porcentaje de bolas al centro"""
    return generate_batted_ball_ranking("straight_rate", "% Centro", "Porcentaje de bolas bateadas hacia el centro del campo.")


@app.get("/rankings/batted-ball-events", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_batted_ball_events():
    """Top 10 por cantidad de eventos de bolas bateadas"""
    return generate_batted_ball_ranking("bbe", "Eventos de Bolas Bateadas", "Total de bolas bateadas en juego. Indica volumen ofensivo.")


@app.get("/rankings/pull-fly-ball-rate", response_model=RankingResponse, tags=["Rankings - Batted Ball"])
async def ranking_pull_fly_ball_rate():
    """Top 10 por porcentaje de fly balls al pull"""
    return generate_batted_ball_ranking("pull_air_rate", "% Aéreas al Pull", "Porcentaje de bolas aéreas (FB+LD) bateadas al side pull. Indica poder al lado preferido.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pybaseball_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
