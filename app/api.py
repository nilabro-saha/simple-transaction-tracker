from fastapi import APIRouter, Depends
from app.db import get_connection
from app.txn_support import (
    fetch_cashflow_by_account,
    fetch_cashflow_overall,
    fetch_balance_by_account,
    fetch_balance_overall
)
import sqlite3
import datetime as dt

router = APIRouter()

@router.get('/cashflow-by-account')
async def cashflow_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_cashflow_by_account(conn, start, end, months)

@router.get('/cashflow')
async def cashflow(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    window:int = 6,
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_cashflow_overall(conn, window, start, end, months)
    
@router.get('/balance-by-account')
async def balance_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_balance_by_account(conn, start, end, months)

@router.get('/balance')
async def balance(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_balance_overall(conn, start, end, months)