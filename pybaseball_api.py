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


class TeamBattingRequest(BaseModel):
    """Parámetros para estadísticas de equipo (bateo)"""
    start_season: int = Field(..., description="Primera temporada")
    end_season: Optional[int] = Field(None, description="Última temporada (opcional)")
    league: str = Field("all", description="Liga")
    ind: int = Field(1, description="1=por temporada, 0=agregado")


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
# RUTAS - ESTADÍSTICAS DE EQUIPO
# ============================================================================

@app.post("/team-batting", response_model=DataframeResponse, tags=["Equipos"])
async def get_team_batting(request: TeamBattingRequest):
    """
    Obtiene estadísticas de bateo a nivel de equipo.

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
        df = pyb.team_batting(
            start_season=request.start_season,
            end_season=request.end_season,
            league=request.league,
            ind=request.ind
        )
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/team-batting-bref/{team}/{start_season}", tags=["Equipos"])
async def get_team_batting_bref(
    team: str = Path(..., description="Ej: NYY, BOS, LAD"),
    start_season: int = Path(..., description="Año inicio"),
    end_season: Optional[int] = Query(None, description="Año fin")
):
    """
    Obtiene estadísticas de bateo de Baseball Reference para un equipo.
    """
    try:
        df = pyb.team_batting_bref(team, start_season, end_season)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/team-pitching", response_model=DataframeResponse, tags=["Equipos"])
async def get_team_pitching(request: TeamBattingRequest):
    """
    Obtiene estadísticas de pitcheo a nivel de equipo.
    """
    try:
        df = pyb.team_pitching(
            start_season=request.start_season,
            end_season=request.end_season,
            league=request.league,
            ind=request.ind
        )
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/team-pitching-bref/{team}/{start_season}", tags=["Equipos"])
async def get_team_pitching_bref(
    team: str,
    start_season: int,
    end_season: Optional[int] = None
):
    """
    Obtiene estadísticas de pitcheo de Baseball Reference para un equipo.
    """
    try:
        df = pyb.team_pitching_bref(team, start_season, end_season)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - WAR (Wins Above Replacement)
# ============================================================================

@app.get("/war-batting", tags=["WAR"])
async def get_war_batting(return_all: bool = False):
    """
    Obtiene datos de WAR para bateadores de Baseball Reference.
    """
    try:
        df = pyb.bwar_bat(return_all)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/war-pitching", tags=["WAR"])
async def get_war_pitching(return_all: bool = False):
    """
    Obtiene datos de WAR para lanzadores de Baseball Reference.
    """
    try:
        df = pyb.bwar_pitch(return_all)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - STANDINGS (Clasificaciones)
# ============================================================================

@app.get("/standings/{season}", tags=["Standings"])
async def get_standings(season: int):
    """
    Obtiene las clasificaciones de división para una temporada.
    Disponible desde 1969.
    """
    try:
        df = pyb.standings(season)
        return dataframe_to_response(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUTAS - SPLITS
# ============================================================================

@app.get("/splits/{playerid}", tags=["Splits"])
async def get_splits(
    playerid: str,
    year: Optional[int] = None,
    pitching_splits: bool = False
):
    """
    Obtiene estadísticas de splits (divididas por categoría) de un jugador.

    **Parámetros:**
    - playerid: ID de Baseball Reference (ej: troutmi01)
    - year: Año específico (opcional, si no se pasa = carrera)
    - pitching_splits: True para splits de pitcheo, False para bateo
    """
    try:
        df = pyb.get_splits(playerid, year, pitching_splits=pitching_splits)
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


def read_sheet_data(sheet_name: str) -> pd.DataFrame:
    """Lee datos de una pestaña de Google Sheets como CSV"""
    try:
        encoded_name = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        logger.info(f"Leyendo: {sheet_name}")
        df = pd.read_csv(url)
        if df.empty:
            logger.warning(f"Sheet {sheet_name} vacío")
            return pd.DataFrame()
        logger.info(f"✓ {sheet_name}: {len(df)} filas")
        return df
    except Exception as e:
        logger.error(f"Error leyendo {sheet_name}: {str(e)}")
        return pd.DataFrame()


def generate_ranking(df: pd.DataFrame, metric_col: str, ranking_id: str, ranking_name: str, top_n: int = 10, ascending: bool = False) -> RankingResponse:
    """Genera un ranking desde datos del dataframe"""
    try:
        if metric_col not in df.columns:
            raise ValueError(f"Columna {metric_col} no existe")
        df_clean = df.dropna(subset=[metric_col])
        if df_clean.empty:
            raise ValueError(f"Sin datos para {ranking_name}")
        df_sorted = df_clean.sort_values(metric_col, ascending=ascending)
        df_top = df_sorted.head(top_n)
        league_avg = df_clean[metric_col].mean()
        league_min = df_clean[metric_col].min()
        league_max = df_clean[metric_col].max()
        top_10_records = []
        for idx, (_, row) in enumerate(df_top.iterrows(), 1):
            percentile = (df_clean[metric_col] <= row[metric_col]).sum() / len(df_clean) * 100
            if 'last_name' in row and 'first_name' in row:
                player_name = f"{row['last_name']}, {row['first_name']}"
            elif 'player_name' in row:
                player_name = str(row['player_name'])
            else:
                player_name = "Unknown"
            top_10_records.append(RankingRecord(rank=idx, player_name=player_name, value=round(float(row[metric_col]), 2), percentile=round(percentile, 1)))
        return RankingResponse(ranking_id=ranking_id, ranking_name=ranking_name, metric=metric_col, top_10=top_10_records, league_avg=round(league_avg, 2) if pd.notna(league_avg) else None, league_min=round(league_min, 2) if pd.notna(league_min) else None, league_max=round(league_max, 2) if pd.notna(league_max) else None, timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ENDPOINTS - RANKINGS (29 RANKINGS DESDE GOOGLE SHEETS)
# ============================================================================

@app.get("/rankings", tags=["Rankings"])
async def list_rankings():
    """Lista todos los rankings disponibles"""
    rankings = {"1": "Exit Velocity", "2": "Expected Stats", "3": "Home Runs", "4": "Percentiles", "5": "Batting Run Value", "6": "Swing Path", "7": "Bat Tracking", "8": "Batting Stance", "9": "Batted Ball", "10": "Pitch Arsenal Stats", "11": "Pitch Tempo", "12": "cat-Catcher Framing", "13": "cat-Pop Time", "14": "cat-Catcher Blocking", "15": "cat-Catcher Stance", "16": "cat-Catcher Throwing", "17": "run-Sprint Speed", "18": "run-Baserunning Run Value", "19": "run-Basestealing Run Value", "20": "run-Extra Bases Taken", "21": "run-90ft Running Splits", "22": "fld-Fielding Run Value", "23": "fld-Arm Strength", "24": "fld-Arm Value", "25": "fld-Outfield Catch Prob", "26": "fld-Outfield Dir OAA", "27": "fld-Outfielder Jump", "28": "fld-Outs Above Average", "29": "Year to Year Changes"}
    return {"available_rankings": rankings, "total": 29, "usage": "GET /rankings/{ranking_id}"}


@app.get("/rankings/{ranking_id}", response_model=RankingResponse, tags=["Rankings"])
async def get_ranking(ranking_id: str = Path(..., description="ID 1-29")):
    """Obtiene un ranking por ID"""
    rankings_map = {"1": ("Exit Velocity", "avg_hit_speed", False), "2": ("Expected Stats", "est_woba", False), "3": ("Home Runs", "xhr", False), "4": ("Percentiles", "xwoba", False), "5": ("Batting Run Value", "runs_all", False), "6": ("Swing Path", "avg_bat_speed", False), "7": ("Bat Tracking", "hard_swing_rate", False), "8": ("Batting Stance", "avg_foot_sep", False), "9": ("Batted Ball", "fb_rate", False), "10": ("Pitch Arsenal Stats", "run_value_per_100", False), "11": ("Pitch Tempo", "median_seconds_empty", True), "12": ("cat-Catcher Framing", "rv_tot", False), "13": ("cat-Pop Time", "pop_2b_sba", True), "14": ("cat-Catcher Blocking", "catcher_blocking_runs", False), "15": ("cat-Catcher Stance", "one_knee_framing_rv", False), "16": ("cat-Catcher Throwing", "rate_cs", False), "17": ("run-Sprint Speed", "sprint_speed", False), "18": ("run-Baserunning Run Value", "runner_runs_tot", False), "19": ("run-Basestealing Run Value", "runs_stolen_on_running_act", False), "20": ("run-Extra Bases Taken", "runner_runs", False), "21": ("run-90ft Running Splits", "seconds_since_hit_090", True), "22": ("fld-Fielding Run Value", "total_runs", False), "23": ("fld-Arm Strength", "max_arm_strength", False), "24": ("fld-Arm Value", "fielder_runs", False), "25": ("fld-Outfield Catch Prob", "oaa", False), "26": ("fld-Outfield Dir OAA", "n_outs_above_average", False), "27": ("fld-Outfielder Jump", "outs_above_average", False), "28": ("fld-Outs Above Average", "outs_above_average", False), "29": ("Year to Year Changes", "delta_2025_2026", False)}
    if ranking_id not in rankings_map:
        raise HTTPException(status_code=404, detail="Ranking no encontrado")
    sheet_name, metric, ascending = rankings_map[ranking_id]
    df = read_sheet_data(sheet_name)
    if df.empty:
        raise HTTPException(status_code=500, detail=f"Error: {sheet_name}")
    return generate_ranking(df, metric, ranking_id, sheet_name, 10, ascending)


@app.get("/rankings/1", response_model=RankingResponse, tags=["Rankings"])
async def get_ranking_1():
    """Obtiene el ranking 1 (Exit Velocity)"""
    try:
        sheet_name = "Exit Velocity"
        encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)
        metric = "avg_hit_speed"
        if metric not in df.columns:
            raise ValueError(f"Columna no encontrada")
        df_clean = df.dropna(subset=[metric])
        df_sorted = df_clean.sort_values(metric, ascending=False)
        df_top = df_sorted.head(10)
        top_10 = []
        names = df_top['last_name, first_name'].tolist()
        values = df_top[metric].tolist()
        for idx, (name, value) in enumerate(zip(names, values), 1):
            pct = (df_clean[metric] <= value).sum() / len(df_clean) * 100
            top_10.append(RankingRecord(rank=idx, player_name=str(name), value=round(float(value), 2), percentile=round(pct, 1)))
        return RankingResponse(ranking_id="1", ranking_name="Exit Velocity", metric="avg_hit_speed", top_10=top_10, league_avg=round(df_clean[metric].mean(), 2), league_min=round(df_clean[metric].min(), 2), league_max=round(df_clean[metric].max(), 2), timestamp=datetime.now().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pybaseball_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
