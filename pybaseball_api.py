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
