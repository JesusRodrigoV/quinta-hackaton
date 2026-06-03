from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_MODES = {"bus", "metro", "walk", "scooter"}
ALLOWED_PREFERENCES = {"time", "cost", "co2"}
SANTIAGO_MIN_LAT = -33.47
SANTIAGO_MAX_LAT = -33.43
SANTIAGO_MIN_LON = -70.67
SANTIAGO_MAX_LON = -70.64


class RouteRequest(BaseModel):
    origin_lat: float = Field(..., description="Latitud del origen", ge=-90, le=90)
    origin_lon: float = Field(..., description="Longitud del origen", ge=-180, le=180)
    dest_lat: float = Field(..., description="Latitud del destino", ge=-90, le=90)
    dest_lon: float = Field(..., description="Longitud del destino", ge=-180, le=180)
    modes: List[str] = Field(
        default=["bus", "metro", "walk", "scooter"],
        description="Modos de transporte permitidos",
    )
    preference: Optional[str] = Field(
        default="time",
        description="Criterio de optimización: time | cost | co2",
    )

    @field_validator("modes")
    @classmethod
    def validate_modes(cls, v):
        for m in v:
            if m not in ALLOWED_MODES:
                raise ValueError(
                    f"Modo inválido: '{m}'. Permitidos: {', '.join(sorted(ALLOWED_MODES))}",
                )
        return v

    @field_validator("preference")
    @classmethod
    def validate_preference(cls, v):
        if v is not None and v not in ALLOWED_PREFERENCES:
            raise ValueError(
                f"Preferencia inválida: '{v}'. Permitidos: {', '.join(sorted(ALLOWED_PREFERENCES))}",
            )
        return v

    @model_validator(mode="after")
    def validate_not_same_point(self):
        dlat = abs(self.origin_lat - self.dest_lat)
        dlon = abs(self.origin_lon - self.dest_lon)
        if dlat < 0.001 and dlon < 0.001:
            raise ValueError("Origen y destino deben ser puntos diferentes")
        return self

    @model_validator(mode="after")
    def validate_in_santiago(self):
        for label, lat, lon in [
            ("Origen", self.origin_lat, self.origin_lon),
            ("Destino", self.dest_lat, self.dest_lon),
        ]:
            if not (SANTIAGO_MIN_LAT <= lat <= SANTIAGO_MAX_LAT
                    and SANTIAGO_MIN_LON <= lon <= SANTIAGO_MAX_LON):
                raise ValueError(
                    f"{label}: las coordenadas ({lat}, {lon}) están fuera del "
                    f"área de cobertura (Santiago, Chile)",
                )
        return self
