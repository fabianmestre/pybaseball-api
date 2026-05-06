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
    description: str
    top_10: List[RankingRecord]
    league_avg: Optional[float] = None
    league_min: Optional[float] = None
    league_max: Optional[float] = None
    timestamp: str


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

        return RankingResponse(
            ranking_id=ranking_name.replace(" ", "-"),
            ranking_name=ranking_name,
            metric=metric,
            description=description,
            top_10=top_10,
            league_avg=round(df_clean[metric].mean(), 2) if len(df_clean) > 0 else None,
            league_min=round(df_clean[metric].min(), 2) if len(df_clean) > 0 else None,
            league_max=round(df_clean[metric].max(), 2) if len(df_clean) > 0 else None,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
# RUTAS - RANKINGS (desde Google Sheets)
# ============================================================================

@app.get("/rankings/bat-speed", response_model=RankingResponse, tags=["Rankings"])
async def ranking_bat_speed():
    """Top 10 por velocidad del bate (Run Value Total)"""
    return generate_ranking("Percentiles", "rv_tot", "Bat Speed", "Velocidad promedio del bate en mph. Correlaciona con poder ofensivo.")


@app.get("/rankings/exit-velocity-percentile", response_model=RankingResponse, tags=["Rankings"])
async def ranking_exit_velocity_percentile():
    """Top 10 por exit velocity percentile"""
    return generate_ranking("Percentiles", "pct_tot", "Exit Velocity Percentile", "Percentil de velocidad de salida. Jugadores en altos percentiles poseen más potencia bruta.")


@app.get("/rankings/barrels", response_model=RankingResponse, tags=["Rankings"])
async def ranking_barrels():
    """Top 10 por barrels (Run Value vs Fastballs)"""
    return generate_ranking("Bat Tracking", "rv_11", "Barrels", "Barrels y contactos de máxima eficiencia. Mide contacto de calidad con máxima potencia.")


@app.get("/rankings/hard-hit-percentile", response_model=RankingResponse, tags=["Rankings"])
async def ranking_hard_hit_percentile():
    """Top 10 por hard hit percent percentile"""
    return generate_ranking("Batted Ball", "pct_11", "Hard Hit % Percentile", "Percentil de porcentaje de golpes duros (exit velocity > 95 mph). Indica consistencia de potencia.")


@app.get("/rankings/barrel-percentage", response_model=RankingResponse, tags=["Rankings"])
async def ranking_barrel_percentage():
    """Top 10 por barrel percentage"""
    return generate_ranking("Expected Stats", "pct_tot", "Barrel %", "Porcentaje de contactos que son barrels. Máxima combinación de ángulo y velocidad de salida.")


@app.get("/rankings/sprint-speed-percentile", response_model=RankingResponse, tags=["Rankings"])
async def ranking_sprint_speed_percentile():
    """Top 10 por sprint speed percentile"""
    return generate_ranking("Home Runs", "pct_tot", "Sprint Speed Percentile", "Percentil de velocidad de carrera. Atletas con altos percentiles tienen mejor velocidad base.")


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
# INICIAR SERVIDOR
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Ejecutar con: python pybaseball_api.py
    # O con: uvicorn pybaseball_api:app --reload
    uvicorn.run(
        "pybaseball_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
