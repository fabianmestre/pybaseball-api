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
import urllib.parse

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
    timestamp: Optional[str] = None


# Google Sheet configuration
GOOGLE_SHEET_ID = "1O9vFxcntbHRa5EUGL-b3yyMwICc2GNSdvwYPLEaTPro"


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


def generate_ranking(sheet_name: str, metric: str, ranking_name: str, description: str, ascending: bool = False) -> RankingResponse:
    """Genera un ranking desde Google Sheets"""
    try:
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        df_clean = df.dropna(subset=[metric]).copy()
        df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
        df_clean = df_clean.dropna(subset=[metric])

        name_col = None
        for candidate in ['name', 'Nombre', 'Jugador', 'Player', 'player_name']:
            if candidate in df_clean.columns:
                name_col = candidate
                break
        if name_col is None and len(df_clean.columns) > 0:
            name_col = df_clean.columns[0]

        df_sorted = df_clean.sort_values(by=metric, ascending=ascending)
        top_10 = []
        for rank, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
            value = round(float(row[metric]), 2) if pd.notna(row[metric]) else None
            player_name = str(row[name_col]) if name_col and name_col in row else 'N/A'
            top_10.append(RankingRecord(
                rank=rank,
                player_name=player_name,
                value=value,
                percentile=round(((len(df_clean) - rank) / len(df_clean)) * 100, 1)
            ))

        return RankingResponse(
            ranking_id=ranking_name.replace(" ", "-"),
            ranking_name=ranking_name,
            metric=metric,
            description=description,
            top_10=top_10,
            league_avg=round(df_clean[metric].mean(), 2) if len(df_clean) > 0 else None,
            league_min=round(df_clean[metric].min(), 2) if len(df_clean) > 0 else None,
            league_max=round(df_clean[metric].max(), 2) if len(df_clean) > 0 else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al generar ranking: {str(e)}")


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
# RUTAS - RANKINGS (desde Google Sheets)
# ============================================================================

# BATEO (4 rankings)
@app.get("/rankings/bat-exit-velocity", response_model=RankingResponse, tags=["Rankings"])
async def ranking_bat_exit_velocity():
    """Top 10 bateadores por exit velocity"""
    return generate_ranking("bat-Percentiles", "exit_velocity", "Exit Velocity", "Velocidad de salida del bate en mph. Indica potencia bruta del bateador.")


@app.get("/rankings/bat-barrels", response_model=RankingResponse, tags=["Rankings"])
async def ranking_bat_barrels():
    """Top 10 bateadores por barrels"""
    return generate_ranking("bat-Exit Velocity", "barrels", "Barrels", "Cantidad de barrels. Contacto óptimo con máxima eficiencia.")


@app.get("/rankings/bat-home-runs", response_model=RankingResponse, tags=["Rankings"])
async def ranking_bat_home_runs():
    """Top 10 bateadores por home runs"""
    return generate_ranking("bat-Home Runs", "hr_total", "Home Runs", "Total de home runs bateados en la temporada.")


@app.get("/rankings/bat-bat-speed", response_model=RankingResponse, tags=["Rankings"])
async def ranking_bat_bat_speed():
    """Top 10 bateadores por velocidad del bate"""
    return generate_ranking("bat-Swing Path", "avg_bat_speed", "Bat Speed", "Velocidad promedio del bate en mph.")


# PITCHEO (4 rankings)
@app.get("/rankings/pit-xera", response_model=RankingResponse, tags=["Rankings"])
async def ranking_pit_xera():
    """Top 10 lanzadores por xERA"""
    return generate_ranking("pit-Percentiles", "xera", "xERA", "ERA esperado. Rendimiento esperado del lanzador.")


@app.get("/rankings/pit-fastball-velocity", response_model=RankingResponse, tags=["Rankings"])
async def ranking_pit_fastball_velocity():
    """Top 10 lanzadores por velocidad de fastball"""
    return generate_ranking("pit-Percentiles", "fb_velocity", "Fastball Velocity", "Velocidad promedio del fastball en mph.")


@app.get("/rankings/pit-pitch-movement", response_model=RankingResponse, tags=["Rankings"])
async def ranking_pit_pitch_movement():
    """Top 10 lanzadores por movimiento de pitches"""
    return generate_ranking("pit-Pitch Movement", "diff_x", "Pitch Movement", "Movimiento horizontal del pitch en pulgadas.")


@app.get("/rankings/pit-active-spin", response_model=RankingResponse, tags=["Rankings"])
async def ranking_pit_active_spin():
    """Top 10 lanzadores por active spin del fastball"""
    return generate_ranking("pit-Active Spin", "active_spin_fourseam", "Active Spin", "Spin activo del fastball. Determina movimiento efectivo.")


# RUNNING (4 rankings)
@app.get("/rankings/run-sprint-speed", response_model=RankingResponse, tags=["Rankings"])
async def ranking_run_sprint_speed():
    """Top 10 corredores por velocidad de carrera"""
    return generate_ranking("run-Sprint Speed", "sprint_speed", "Sprint Speed", "Velocidad de carrera en ft/s. Velocidad máxima en línea recta.")


@app.get("/rankings/run-baserunning-value", response_model=RankingResponse, tags=["Rankings"])
async def ranking_run_baserunning_value():
    """Top 10 corredores por valor de base running"""
    return generate_ranking("run-Baserunning Run Value", "runner_runs_tot", "Baserunning Value", "Valor total en carreras por base running.")


@app.get("/rankings/run-basestealing-value", response_model=RankingResponse, tags=["Rankings"])
async def ranking_run_basestealing_value():
    """Top 10 corredores por robo de bases"""
    return generate_ranking("run-Basestealing Run Value", "runs_stolen_on_running_act", "Basestealing Value", "Valor en carreras por robo de bases exitoso.")


@app.get("/rankings/run-extra-bases", response_model=RankingResponse, tags=["Rankings"])
async def ranking_run_extra_bases():
    """Top 10 corredores por bases extra tomadas"""
    return generate_ranking("run-Extra Bases Taken", "runner_runs", "Extra Bases Taken", "Valor en carreras por tomar bases extra.")


# CATCHING (4 rankings)
@app.get("/rankings/cat-framing", response_model=RankingResponse, tags=["Rankings"])
async def ranking_cat_framing():
    """Top 10 catchers por framing"""
    return generate_ranking("cat-Catcher Framing", "rv_tot", "Catcher Framing", "Valor en carreras por framing de pitches.")


@app.get("/rankings/cat-pop-time", response_model=RankingResponse, tags=["Rankings"])
async def ranking_cat_pop_time():
    """Top 10 catchers por pop time"""
    return generate_ranking("cat-Pop Time", "pop_2b_sba", "Pop Time", "Tiempo promedio de pop time a segunda base en segundos.")


@app.get("/rankings/cat-throwing", response_model=RankingResponse, tags=["Rankings"])
async def ranking_cat_throwing():
    """Top 10 catchers por arm strength"""
    return generate_ranking("cat-Catcher Throwing", "arm_strength", "Throwing", "Fuerza de brazo del catcher. Velocidad de lanzamiento.")


@app.get("/rankings/cat-blocking", response_model=RankingResponse, tags=["Rankings"])
async def ranking_cat_blocking():
    """Top 10 catchers por bloqueo de pitches"""
    return generate_ranking("cat-Catcher Blocking", "catcher_blocking_runs", "Blocking", "Valor en carreras por bloqueo de pitches en la suciedad.")


# FIELDING (4 rankings)
@app.get("/rankings/fld-outs-above-average", response_model=RankingResponse, tags=["Rankings"])
async def ranking_fld_outs_above_average():
    """Top 10 defensores por outs above average"""
    return generate_ranking("fld-Outs Above Average", "outs_above_average", "Outs Above Average", "Outs por encima del promedio. Métrica de defensa.")


@app.get("/rankings/fld-arm-strength", response_model=RankingResponse, tags=["Rankings"])
async def ranking_fld_arm_strength():
    """Top 10 defensores por arm strength"""
    return generate_ranking("fld-Arm Strength", "max_arm_strength", "Arm Strength", "Fuerza de brazo máxima en mph.")


@app.get("/rankings/fld-fielding-runs", response_model=RankingResponse, tags=["Rankings"])
async def ranking_fld_fielding_runs():
    """Top 10 defensores por valor de defensa"""
    return generate_ranking("fld-Fielding Run Value", "total_runs", "Fielding Runs", "Carreras evitadas por defensa total.")


@app.get("/rankings/fld-catch-probability", response_model=RankingResponse, tags=["Rankings"])
async def ranking_fld_catch_probability():
    """Top 10 outfielders por probabilidad de catch"""
    return generate_ranking("fld-Outfield Catch Prob", "n_5star_percent", "Catch Probability", "Porcentaje de atrapadas en plays de 5 estrellas.")


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
            "rankings": "/rankings/bat-exit-velocity, /rankings/pit-xera, /rankings/run-sprint-speed, etc (20 total)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pybaseball_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
