"""Camada ACS (resumo, workbench, actions). Paths TR-069 ficam em `app.cpe`."""

from app.acs.summary import DEVICE_DETAIL_PROJECTION, build_workbench, device_summary

__all__ = [
    "DEVICE_DETAIL_PROJECTION",
    "build_workbench",
    "device_summary",
]
