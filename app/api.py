from fastapi import APIRouter, Depends, Query
from app.db import get_connection
from app.txn_support import (
    fetch_accounts,
    fetch_monthly_account_stats,
    fetch_cashflow_by_account,
    fetch_cashflow_overall,
    fetch_balance_by_account,
    fetch_balance_overall,
    fetch_stat_months
)
from app.txn_support import OverallBalance, OverallCashflow
import sqlite3
import datetime as dt
from typing import Literal, Optional
from pydantic import BaseModel
from dataclasses import dataclass
from typing import Any
from app.utils import generate_linear_model

router = APIRouter()

@router.get('/accounts')
async def accounts(conn:sqlite3.Connection=Depends(get_connection)):
    return fetch_accounts(conn)

@router.get('/stats')
async def monthly_stats(
    start:dt.date|None = None,
    end:dt.date|None = None,
    month:list[str] = Query([]),
    conn:sqlite3.Connection=Depends(get_connection)
):
    print(month)
    return fetch_monthly_account_stats(conn, start, end, month)

@router.get('/cashflow-by-account')
async def cashflow_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    month:list[str] = Query([]),
    conn:sqlite3.Connection=Depends(get_connection)
):
    print(month)
    return fetch_cashflow_by_account(conn, start, end, month).create_json()

@router.get('/cashflow')
async def cashflow(
    start:dt.date|None = None,
    end:dt.date|None = None,
    month:list[str] = Query([]),
    window:int = 6,
    conn:sqlite3.Connection=Depends(get_connection)
):
    print(month)
    cashflows = fetch_cashflow_overall(conn, window, start, end, month)
    return OverallCashflow.create_json(cashflows, window)
    
@router.get('/balance-by-account')
async def balance_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    month:list[str] = Query([]),
    conn:sqlite3.Connection=Depends(get_connection)
):
    print(month)
    return fetch_balance_by_account(conn, start, end, month).create_json()

@router.get('/balance')
async def balance(
    start:dt.date|None = None,
    end:dt.date|None = None,
    month:list[str] = Query([]),
    conn:sqlite3.Connection=Depends(get_connection)
):
    print(month)
    balances = fetch_balance_overall(conn, start, end, month)
    return OverallBalance.create_json(balances)

@router.get('/months')
async def months(
    start:dt.date|None = None,
    end:dt.date|None = None,
    sort:Literal['asc','desc'] = 'asc',
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_stat_months(start, end, sort, conn)

@dataclass
class RegressionRequest(BaseModel):
    x:list[Any]
    y:list[float]
    extend:int=0

@router.post('/trendline/')
async def trendline(request:RegressionRequest):
    return generate_linear_model(request.x, request.y, request.extend)