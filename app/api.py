from fastapi import APIRouter, Depends
from app.db import get_connection
from app.txn_support import (
    fetch_accounts,
    fetch_monthly_account_stats,
    fetch_cashflow_by_account,
    fetch_cashflow_overall,
    fetch_balance_by_account,
    fetch_balance_overall
)
from app.txn_support import OverallBalance, OverallCashflow
import sqlite3
import datetime as dt

router = APIRouter()

@router.get('/accounts')
async def accounts(conn:sqlite3.Connection=Depends(get_connection)):
    return fetch_accounts(conn)

@router.get('/stats')
async def monthly_stats(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_monthly_account_stats(conn, start, end, months)

@router.get('/cashflow-by-account')
async def cashflow_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_cashflow_by_account(conn, start, end, months).create_json()

@router.get('/cashflow')
async def cashflow(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    window:int = 6,
    conn:sqlite3.Connection=Depends(get_connection)
):
    cashflows = fetch_cashflow_overall(conn, window, start, end, months)
    return OverallCashflow.create_json(cashflows, window)
    
@router.get('/balance-by-account')
async def balance_by_account(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    return fetch_balance_by_account(conn, start, end, months).create_json()

@router.get('/balance')
async def balance(
    start:dt.date|None = None,
    end:dt.date|None = None,
    months:list[str] = [],
    conn:sqlite3.Connection=Depends(get_connection)
):
    balances = fetch_balance_overall(conn, start, end, months)
    return OverallBalance.create_json(balances)