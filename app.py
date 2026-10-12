# app.py — E-Soccer Fifa Analytics v6.13.0
# (Playwright para Cloudflare + Cache MC + Hero IN ALGORITHM)
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import re
import math
import base64
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from collections import Counter
from io import BytesIO

# Instala Chromium na primeira execução (Streamlit Cloud)
try:
    os.system("playwright install chromium 2>/dev/null")
except Exception:
    pass

from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import streamlit.components.v1 as components

if not hasattr(st, 'fragment'):
    def _fake_fragment(*args, **kwargs):
        def deco(fn): return fn
        return deco
    st.fragment = _fake_fragment

st.set_page_config(page_title="E-Soccer Fifa Analytics | FIFAlgorithm", page_icon="🤖",
                   layout="wide", initial_sidebar_state="expanded")

if 'modo_claro' not in st.session_state: st.session_state.modo_claro = False
if 'som_ativo' not in st.session_state: st.session_state.som_ativo = True
if 'notif_alerta' not in st.session_state: st.session_state.notif_alerta = True
if 'ultima_oportunidade' not in st.session_state: st.session_state.ultima_oportunidade = set()
if 'page' not in st.session_state: st.session_state.page = 'jogos_dia'
if '_fetch_errors' not in st.session_state: st.session_state['_fetch_errors'] = []
if '_profile_cache' not in st.session_state: st.session_state['_profile_cache'] = {}

N_SIMULATIONS = 5000
H2H_RECENCY = 0.85
H2H_MAX_WEIGHT = 0.70
H2H_FULL_TRUST_N = 10
HT_FACTOR = 0.45
SHRINKAGE_K = 6.0
DC_RHO = -0.10
DC_MAX_GOALS = 8
HT_OVER_25_THRESHOLD = 5.50
RADAR_GAMES = 10
ACEODDS_TIMEOUT = 45
ACEODDS_MAX_RETRIES = 3
FORM_GAMES = 5

SAFE_LINE_TABLE = [
    (6.70, 'Over 5.5', 'MUITA alta'), (5.70, 'Over 4.5', 'alta'),
    (4.50, 'Over 3.5', 'boa'), (3.45, 'Over 2.5', 'média'),
    (2.40, 'Over 1.5', 'baixa'), (2.00, 'Over 0.5', 'muito baixa'),
]

LEAGUES = {
    'Battle - 8 Min': {'id': '179369', 'icon': '🎮'},
    'Battle Volta - 6 Min': {'id': '179371', 'icon': '🎮'},
    'GT League – 12 Min': {'id': '179375', 'icon': '🎮'},
    'H2H GG - 8 Min': {'id': '179367', 'icon': '🎮'},
    'Adriatic - 10 Min': {'id': '179373', 'icon': '🎮'}
}

LEAGUE_NAME_MAP = {
    'E-Soccer - Battle - 8 minutos de jogo': 'Battle - 8 Min',
    'E-Soccer - H2H GG League - 8 minutos de jogo': 'H2H GG - 8 Min',
    'E-Soccer - Battle Volta - 6 minutos de jogo': 'Battle Volta - 6 Min',
    'E-Soccer - GT Leagues - 12 minutos de jogo': 'GT League – 12 Min',
    'E-Soccer - Adriatic - 10 minutos de jogo': 'Adriatic - 10 Min',
}

EXTRA_COLUMNS = [
    'Gols HT', 'Over 0.5 HT', 'Over 1.5 HT', 'Over 2.5 HT', 'BTTS HT',
    'Gols FT', 'Over 0.5 FT', 'Over 1.5 FT', 'Over 2.5 FT',
    'Over 3.5 FT', 'Over 4.5 FT', 'Over 5.5 FT', 'BTTS FT',
    'O1.5 Jogador', 'O2.5 Jogador',
    'xG Casa', 'xG Fora', 'Linha Seg FT', 'O2.5 HT?', 'Conf',
    'Prob Casa', 'Prob Empate', 'Prob Fora',
    'Rec HT', 'Prob Rec HT'
]


# ============================================
# CSS — DARK NEON THEME
# ============================================
def get_css(modo_claro=False):
    bg_card2 = "rgba(20,25,45,0.65)"
    txt = "#f0f5ff"
    txt_dim = "#7a89a8"
    border = "rgba(0,229,255,0.22)"
    accent = "#00f5ff"
    accent2 = "#b537ff"
    bg_gradient = ("radial-gradient(circle at 15% 0%, rgba(0,245,255,0.09), transparent 45%), "
                   "radial-gradient(circle at 85% 100%, rgba(181,55,255,0.09), transparent 45%), "
                   "radial-gradient(circle at 50% 50%, rgba(0,255,136,0.03), transparent 60%), #05070f")
    sidebar_bg = "linear-gradient(180deg, #070a14 0%, #05070f 100%)"
    sidebar_border = "rgba(0,245,255,0.18)"

    base = f"""<style>
* {{ font-family: 'Inter', -apple-system, sans-serif; }}
.stApp {{ background: {bg_gradient}; }}
html, body {{ margin: 0 !important; padding: 0 !important; }}
.stApp {{ margin-top: 0 !important; padding-top: 0 !important; }}
[data-testid="stAppViewContainer"] {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stAppViewContainer"] > .main {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stAppViewContainer"] .main .block-container {{
    padding-top: 0 !important; margin-top: -30px !important;
    padding-bottom: 0.1rem !important; padding-left: 0.8rem !important;
    padding-right: 0.8rem !important; max-width: 100% !important;
}}
[data-testid="stHeader"], .stApp > header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
    display: none !important; height: 0 !important; min-height: 0 !important;
}}
section.main {{ padding-top: 0 !important; margin-top: 0 !important; }}
section.main > div:first-child {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stVerticalBlock"] {{ gap: 0.55rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ padding: 0 !important; }}
[data-testid="stVerticalBlock"] > div:first-child {{ margin-top: 0 !important; padding-top: 0 !important; }}
.main .block-container > div > [data-testid="stVerticalBlock"]:first-child > div:first-child {{
    margin-top: 0 !important; padding-top: 0 !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {accent} 0%, {accent2} 100%) !important;
    border: none !important; color: #05070f !important;
    font-weight: 800 !important; border-radius: 8px !important;
    padding: 6px 14px !important; font-size: 12.5px !important;
    box-shadow: 0 0 22px rgba(0,245,255,0.45), 0 0 40px rgba(181,55,255,0.25) !important;
    transition: all 0.2s !important; height: 32px !important;
    min-height: 32px !important; letter-spacing: 0.3px;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 0 32px rgba(0,245,255,0.7), 0 0 60px rgba(181,55,255,0.4) !important;
    transform: translateY(-1px);
}}
.stButton > button {{
    background: {bg_card2} !important; border: 1px solid {border} !important;
    color: {txt} !important; border-radius: 8px !important;
    font-weight: 700 !important; padding: 6px 14px !important;
    font-size: 12.5px !important; transition: all 0.2s !important;
    height: 32px !important; min-height: 32px !important;
}}
.stButton > button:hover {{
    border-color: {accent} !important; color: {accent} !important;
    box-shadow: 0 0 18px rgba(0,245,255,0.35) !important;
}}
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: linear-gradient(180deg, {accent}, {accent2}); border-radius: 4px;
                             box-shadow: 0 0 8px rgba(0,245,255,0.5); }}
[data-testid="stSidebar"] {{ background: {sidebar_bg} !important; border-right: 1px solid {sidebar_border}; }}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0.5rem !important; }}
.sb-brand {{ display: flex; align-items: center; gap: 12px;
    padding: 14px 14px 18px 14px;
    border-bottom: 1px solid {sidebar_border}; margin-bottom: 10px; }}
.sb-logo {{ width: 40px; height: 40px; border-radius: 10px;
    background: linear-gradient(135deg, {accent}, {accent2});
    display: flex; align-items: center; justify-content: center; font-size: 20px;
    box-shadow: 0 0 24px rgba(0,245,255,0.5), 0 0 50px rgba(181,55,255,0.3); }}
.sb-brand-name {{ font-size: 14px; font-weight: 900;
    background: linear-gradient(135deg, {accent}, {accent2});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 10px rgba(0,245,255,0.5)); }}
.sb-brand-sub {{ font-size: 10.5px; color: {txt_dim}; margin-top: 2px; font-weight: 600; }}
.sb-section {{ font-size: 10px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 1px; color: {txt_dim}; padding: 12px 14px 6px 14px; }}
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important; border: none !important;
    color: {txt_dim} !important; border-radius: 8px !important;
    font-weight: 700 !important; padding: 10px 14px !important;
    font-size: 13.5px !important; text-align: left !important;
    justify-content: flex-start !important; transition: all 0.15s !important;
    margin-bottom: 2px !important; height: auto !important; min-height: auto !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(0,245,255,0.1) !important; color: {accent} !important;
    text-shadow: 0 0 10px rgba(0,245,255,0.6);
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: rgba(0,245,255,0.14) !important; color: {accent} !important;
    border-left: 3px solid {accent} !important;
    border-radius: 0 8px 8px 0 !important;
    box-shadow: 0 0 20px rgba(0,245,255,0.25) !important;
    text-shadow: 0 0 10px rgba(0,245,255,0.6);
}}
.sb-footer {{ padding: 12px 14px; border-top: 1px solid {sidebar_border};
    margin-top: 16px; font-size: 11px; color: {txt_dim}; }}
.sb-footer-user {{ display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border-radius: 8px;
    background: rgba(0,245,255,0.05); border: 1px solid {sidebar_border}; margin-top: 8px; }}
.sb-avatar {{ width: 28px; height: 28px; border-radius: 50%;
    background: linear-gradient(135deg, {accent}, {accent2});
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 900; color: #05070f;
    box-shadow: 0 0 16px rgba(0,245,255,0.5); }}
div[data-baseweb="select"] > div {{ background: {bg_card2} !important; border: 1px solid {border} !important;
    border-radius: 8px !important; color: {txt} !important; min-height: 32px !important;
    font-size: 12.5px !important; }}
div[data-baseweb="select"] svg {{ fill: {accent} !important; }}
.pbar {{ height: 8px; background: rgba(0,245,255,0.06); border-radius: 100px;
    overflow: hidden; margin-top: 6px; }}
.pbar > div {{ height: 100%; border-radius: 100px; }}
.prog-row {{ display: grid; grid-template-columns: 70px 75px 1fr; gap: 14px;
    align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(0,245,255,0.06); }}
.prog-lbl {{ font-size: 14px; font-weight: 700; color: {txt};
    font-family: 'JetBrains Mono', monospace; }}
.prog-val {{ font-size: 14px; font-weight: 800; font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 8px currentColor; }}
.section-label {{ font-size: 12px; font-weight: 900; text-transform: uppercase;
    letter-spacing: 1.2px; color: {accent}; margin: 14px 0 10px 0;
    display: flex; align-items: center; gap: 8px;
    text-shadow: 0 0 12px rgba(0,245,255,0.5); }}
.section-label::before {{ content: ''; width: 3px; height: 14px;
    background: linear-gradient(180deg, {accent}, {accent2}); border-radius: 2px;
    box-shadow: 0 0 10px {accent}; }}
[data-testid="stDataFrame"] {{ background: {bg_card2}; border-radius: 12px; border: 1px solid {border}; }}
.stAlert {{ background: {bg_card2} !important; border-radius: 10px !important;
    border: 1px solid {border} !important; font-size: 13px !important;
    padding: 6px 12px !important; }}
details > summary {{
    background: rgba(20,25,45,0.5) !important; border: 1px solid {border} !important;
    border-radius: 8px !important; padding: 4px 10px !important;
    color: {txt_dim} !important; font-size: 11px !important;
    font-weight: 700 !important; cursor: pointer !important;
    margin: 2px 0 !important; list-style: none !important;
}}
details[open] > summary {{ border-color: {accent} !important; color: {accent} !important;
    background: rgba(0,245,255,0.08) !important; }}
.h2h-card {{
    background: linear-gradient(135deg, rgba(8,12,25,0.98), rgba(15,20,40,0.95));
    border: 1px solid rgba(0,245,255,0.3); border-radius: 14px;
    padding: 18px 20px; margin-top: 10px; margin-bottom: 20px;
    box-shadow: 0 0 30px rgba(0,245,255,0.1), inset 0 0 30px rgba(0,245,255,0.02);
}}
.h2h-header {{ display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid rgba(0,245,255,0.15); padding-bottom: 12px; margin-bottom: 14px; }}
.h2h-team {{ display: flex; flex-direction: column; gap: 6px; flex: 1; }}
.h2h-team.right {{ align-items: flex-end; text-align: right; }}
.h2h-team-name {{ font-size: 20px; font-weight: 900; color: #f0f5ff;
    letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px; }}
.h2h-team.right .h2h-team-name {{ flex-direction: row-reverse; }}
.h2h-team-form {{ display: flex; gap: 4px; }}
.h2h-match-info {{ text-align: center; display: flex;
    flex-direction: column; gap: 4px; padding: 0 20px; }}
.h2h-match-info .vs {{ font-size: 24px; font-weight: 900; color: #00f5ff;
    text-shadow: 0 0 14px rgba(0,245,255,0.6); }}
.h2h-match-info .league {{ font-size: 10px; color: #7a89a8; font-weight: 800;
    text-transform: uppercase; letter-spacing: 1px; }}
.h2h-table {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
.h2h-col {{ display: flex; flex-direction: column; gap: 8px; }}
.h2h-row {{ display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid rgba(0,245,255,0.05); }}
.h2h-row-label {{ font-size: 10.5px; color: #7a89a8; font-weight: 700;
    width: 105px; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.5px; }}
.h2h-row-seq {{ display: flex; gap: 4px; flex: 1; justify-content: center; flex-wrap: nowrap; overflow: hidden; }}
.h2h-seq-item {{ width: 22px; height: 22px; border-radius: 6px;
    font-size: 10.5px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    background: rgba(0,245,255,0.08); border: 1px solid rgba(0,245,255,0.2);
    color: #f0f5ff; font-family: 'JetBrains Mono', monospace; flex-shrink: 0; }}
.h2h-seq-item.highlight {{ background: rgba(0,255,136,0.15);
    border-color: rgba(0,255,136,0.5); color: #00ff88; }}
.h2h-seq-item.ht-hl {{ background: rgba(181,55,255,0.15);
    border-color: rgba(181,55,255,0.5); color: #c77dff; }}
.h2h-row-avg {{ font-size: 13px; font-weight: 900; color: #00f5ff;
    font-family: 'JetBrains Mono', monospace; width: 42px; text-align: right; flex-shrink: 0; }}
.h2h-row-avg.ht {{ color: #b537ff; }}
.h2h-row-avg.ft {{ color: #00ff88; }}
.league-card {{ padding: 14px 18px; margin: 8px 0; border-radius: 12px;
    background: {bg_card2}; border: 1px solid {border}; border-left: 3px solid {accent};
    box-shadow: 0 0 20px rgba(0,245,255,0.08); }}
.league-card-best {{
    padding: 18px 22px; margin: 10px 0 16px 0; border-radius: 14px;
    background: linear-gradient(135deg, rgba(0,255,136,0.12) 0%, rgba(0,245,255,0.08) 100%);
    border: 2px solid rgba(0,255,136,0.55);
    box-shadow: 0 0 40px rgba(0,255,136,0.35), inset 0 0 40px rgba(0,255,136,0.08);
    position: relative; overflow: hidden;
    animation: glow-best 2.5s ease-in-out infinite alternate;
}}
@keyframes glow-best {{
    0% {{ box-shadow: 0 0 40px rgba(0,255,136,0.35), inset 0 0 40px rgba(0,255,136,0.08); }}
    100% {{ box-shadow: 0 0 60px rgba(0,255,136,0.6), inset 0 0 50px rgba(0,255,136,0.15); }}
}}
.best-badge {{ display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 100px;
    background: linear-gradient(135deg, #00ff88, #00cc6a); color: #05070f;
    font-size: 11px; font-weight: 900; letter-spacing: 0.6px; text-transform: uppercase;
    box-shadow: 0 0 20px rgba(0,255,136,0.6); }}
.best-reason {{ margin-top: 12px; padding: 10px 14px; border-radius: 10px;
    background: rgba(0,255,136,0.08); border-left: 3px solid #00ff88;
    font-size: 13px; line-height: 1.6; color: {txt}; }}
.best-reason b {{ color: #00ff88; }}
.best-reason .hl {{ color: {accent}; font-weight: 800; }}
.thermometer {{ height: 6px; border-radius: 100px; background: rgba(0,245,255,0.08);
    margin-top: 8px; overflow: hidden; border: 1px solid {border}; }}
.thermometer > div {{ height: 100%; background: linear-gradient(90deg, {accent2}, {accent});
    box-shadow: 0 0 12px {accent}; }}
.badge-ofensivo {{ background: linear-gradient(135deg, #00ff88, #00cc6a); color: #05070f;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.badge-equilibrado {{ background: linear-gradient(135deg, {accent}, #0099cc); color: #05070f;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.badge-defensivo {{ background: linear-gradient(135deg, {accent2}, #7c3aed); color: #fff;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.badge-ht-heavy {{ background: linear-gradient(135deg, #ff8c00, #ff2e88); color: #fff;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.badge-ft-heavy {{ background: linear-gradient(135deg, #00f5ff, #0099cc); color: #05070f;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.badge-balanced {{ background: linear-gradient(135deg, #7a89a8, #4a5568); color: #fff;
    padding: 4px 12px; border-radius: 100px; font-size: 10.5px; font-weight: 900; }}
.dual-bar {{ display: flex; height: 8px; border-radius: 100px;
    overflow: hidden; margin-top: 10px;
    border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3); }}
.dual-bar .ht {{ background: linear-gradient(90deg, #ff8c00, #ff2e88); }}
.dual-bar .ft {{ background: linear-gradient(90deg, #00f5ff, #b537ff); }}
.rank-list {{ display: flex; flex-direction: column; gap: 4px; margin-top: 8px; }}
.rank-header, .rank-row {{ display: grid; gap: 6px; align-items: center;
    padding: 8px 12px; border-radius: 8px; }}
.rank-header.r1, .rank-row.r1 {{ grid-template-columns: 44px minmax(120px, 1.2fr) 42px minmax(200px, 2fr) 60px 60px 60px 60px 60px; }}
.rank-header.r2, .rank-row.r2 {{ grid-template-columns: 44px minmax(140px, 1.5fr) 42px 90px 90px 90px 90px; }}
.rank-header.r3, .rank-row.r3 {{ grid-template-columns: 44px minmax(130px, 1.4fr) 42px 75px 75px 75px 75px 75px 75px 85px; }}
.rank-header.r4, .rank-row.r4 {{ grid-template-columns: 44px minmax(140px, 1.5fr) 42px 80px 120px 120px; }}
.rank-header {{ background: linear-gradient(135deg, rgba(0,245,255,0.12), rgba(181,55,255,0.08));
    border: 1px solid rgba(0,245,255,0.4); padding: 10px 12px; }}
.rank-hcell {{ font-size: 10px; font-weight: 900; color: #00f5ff;
    text-transform: uppercase; letter-spacing: 0.5px; text-align: center;
    text-shadow: 0 0 8px rgba(0,245,255,0.5); white-space: nowrap; }}
.rank-row {{ background: rgba(15,20,35,0.85);
    border: 1px solid rgba(0,245,255,0.15); }}
.rank-pos {{ font-size: 15px; font-weight: 900; text-align: center; }}
.rank-name {{ font-size: 13px; font-weight: 900; color: #f0f5ff;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.rank-num {{ font-size: 12.5px; font-weight: 800;
    font-family: 'JetBrains Mono', monospace; text-align: center; color: #f0f5ff; }}
.rank-form {{ display: flex; gap: 3px; justify-content: center; }}
.lp-market-card {{ position: relative; padding: 16px 18px; border-radius: 14px;
    background: linear-gradient(135deg, rgba(0,245,255,0.05) 0%, rgba(181,55,255,0.04) 100%);
    border: 1px solid rgba(0,245,255,0.3); margin-bottom: 10px; }}
.lp-market-card .lp-title {{ font-size: 13px; font-weight: 900; color: #f0f5ff;
    text-transform: uppercase; letter-spacing: 1px;
    display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
.lp-market-card .lp-row {{ display: flex; justify-content: space-between;
    font-size: 12.5px; padding: 4px 0; color: #7a89a8; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
.hero-v2 {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 20px 28px; margin-bottom: 16px;
    background: linear-gradient(135deg, rgba(5,8,20,0.98) 0%, rgba(10,15,30,0.98) 100%);
    border: 1.5px solid rgba(0,245,255,0.4); border-radius: 14px;
    box-shadow: 0 0 50px rgba(0,245,255,0.15);
    position: relative; overflow: hidden;
}}
.hero-v2::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #00f5ff, #b537ff, #00f5ff, transparent);
    box-shadow: 0 0 25px rgba(0,245,255,0.9); }}
.hero-v2-left {{ display: flex; align-items: center; gap: 22px; }}
.hero-v2-logo {{ width: 76px; height: 76px;
    display: flex; align-items: center; justify-content: center; font-size: 52px;
    filter: drop-shadow(0 0 25px rgba(0,245,255,0.9)) drop-shadow(0 0 45px rgba(181,55,255,0.5));
    animation: heroLogoPulse 3s ease-in-out infinite; }}
@keyframes heroLogoPulse {{
    0%,100% {{ filter: drop-shadow(0 0 25px rgba(0,245,255,0.9)); transform: scale(1); }}
    50%     {{ filter: drop-shadow(0 0 35px rgba(181,55,255,1)); transform: scale(1.03); }}
}}
.hero-v2-title-block {{ display: flex; flex-direction: column; gap: 8px; }}
.hero-v2-title {{ font-size: 36px; font-weight: 900; letter-spacing: -0.8px;
    color: #f0f5ff; text-shadow: 0 0 35px rgba(0,245,255,0.5);
    line-height: 1; font-style: italic;
    display: flex; align-items: center; gap: 12px; }}
.hero-v2-title .bolt {{ color: #00f5ff; font-style: normal; }}
.hero-v2-accent {{ background: linear-gradient(135deg, #00f5ff 0%, #b537ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.hero-v2-tagline {{ display: flex; align-items: center; gap: 12px;
    font-size: 11.5px; font-weight: 700; }}
.hero-v2-at {{ color: #00f5ff; font-weight: 900; font-size: 13px;
    text-shadow: 0 0 14px rgba(0,245,255,0.9); }}
.hero-v2-tag-sep {{ color: #3a4a6a; font-size: 14px; }}
.hero-v2-tag-text {{ color: #7a89a8; letter-spacing: 1.2px; }}
.hero-v2-right {{ display: flex; align-items: center; gap: 22px; }}
.hero-v2-right-text {{ text-align: right; }}
.hero-v2-rl1 {{ font-size: 13.5px; font-weight: 800;
    color: #f0f5ff; letter-spacing: 2px; }}
.hero-v2-rl2 {{ font-size: 17px; font-weight: 900;
    letter-spacing: 2px; color: #f0f5ff; margin-top: 2px; }}
.hero-v2-hl {{ background: linear-gradient(135deg, #00f5ff, #b537ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.hero-v2-badge {{ width: 78px; height: 78px; border-radius: 20px;
    background: linear-gradient(135deg, rgba(8,12,25,0.98), rgba(15,20,40,0.98));
    border: 2px solid rgba(0,245,255,0.55);
    display: flex; align-items: center; justify-content: center;
    position: relative;
    box-shadow: 0 0 30px rgba(0,245,255,0.45);
    animation: badgePulse 3s ease-in-out infinite; overflow: hidden; flex-shrink: 0; }}
.hero-v2-badge::before {{ content: ''; position: absolute; inset: -50%;
    background: conic-gradient(from 0deg, transparent, #00f5ff, transparent, #b537ff, transparent);
    animation: badgeRotate 4s linear infinite; opacity: 0.45; z-index: 0; }}
.hero-v2-badge::after {{ content: ''; position: absolute; inset: 2px; border-radius: 16px;
    background: linear-gradient(135deg, rgba(8,12,25,0.99), rgba(15,20,40,0.99)); z-index: 1; }}
.hero-v2-badge .badge-emoji {{ position: relative; z-index: 2; font-size: 40px;
    filter: drop-shadow(0 0 14px rgba(0,245,255,0.9)); }}
@keyframes badgePulse {{
    0%,100% {{ box-shadow: 0 0 30px rgba(0,245,255,0.45); }}
    50%     {{ box-shadow: 0 0 48px rgba(181,55,255,0.75); }}
}}
@keyframes badgeRotate {{ to {{ transform: rotate(360deg); }} }}
.info-v2-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 12px; margin-bottom: 14px; }}
.info-v2-card {{ display: flex; align-items: center; gap: 14px;
    padding: 14px 20px;
    background: linear-gradient(135deg, rgba(8,12,25,0.92) 0%, rgba(15,20,40,0.92) 100%);
    border: 1.5px solid rgba(0,245,255,0.35); border-radius: 12px;
    position: relative; overflow: hidden; }}
.info-v2-card::before {{ content: ''; position: absolute; top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #00f5ff, #b537ff); }}
.info-v2-icon {{ width: 46px; height: 46px; border-radius: 11px;
    background: linear-gradient(135deg, rgba(0,245,255,0.18), rgba(181,55,255,0.14));
    border: 1px solid rgba(0,245,255,0.35);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0; }}
.info-v2-content {{ display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
.info-v2-label {{ font-size: 9.5px; font-weight: 900; color: #7a89a8;
    text-transform: uppercase; letter-spacing: 1.6px; }}
.info-v2-value {{ font-size: 26px; font-weight: 900;
    background: linear-gradient(135deg, #ffffff, #00f5ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1; letter-spacing: -0.5px; }}
.info-v2-value.purple {{
    background: linear-gradient(135deg, #ffffff, #b537ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.info-v2-sub {{ font-size: 10px; font-weight: 800; color: #7a89a8;
    letter-spacing: 1px; margin-top: 2px; }}
.info-v2-prob-text {{ font-size: 13px; font-weight: 800; color: #00f5ff;
    font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 12px rgba(0,245,255,0.6); }}
.info-v2-online {{ margin-left: auto;
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 14px; background: rgba(0,255,136,0.1);
    border: 1px solid rgba(0,255,136,0.45); border-radius: 100px;
    font-size: 10px; font-weight: 900; color: #00ff88; letter-spacing: 1.2px; }}
.info-v2-dot {{ width: 7px; height: 7px; border-radius: 50%;
    background: #00ff88; box-shadow: 0 0 12px #00ff88; animation: pulse 2s infinite; }}
@keyframes pulse {{
    0%,100% {{ opacity: 1; transform: scale(1); }}
    50%     {{ opacity: 0.5; transform: scale(1.2); }}
}}
.match-v2-header, .match-v2-row {{
    display: grid;
    grid-template-columns: 135px 320px 115px 130px 130px minmax(400px, 1fr);
    gap: 6px;
}}
.match-v2-header {{ padding: 9px 10px;
    background: linear-gradient(135deg, rgba(0,245,255,0.1), rgba(181,55,255,0.06));
    border: 1.5px solid rgba(0,245,255,0.45);
    border-radius: 10px; margin-bottom: 5px; }}
.mvh-cell {{ font-size: 10px; font-weight: 900; color: #00f5ff;
    text-transform: uppercase; letter-spacing: 0.9px; text-align: center;
    display: flex; align-items: center; justify-content: center; }}
.match-v2-row {{ padding: 7px 10px;
    background: linear-gradient(135deg, rgba(8,12,25,0.92) 0%, rgba(12,18,35,0.88) 100%);
    border: 1.5px solid rgba(0,245,255,0.22); border-radius: 10px; margin-bottom: 5px;
    align-items: stretch; }}
.mv-box {{ display: flex; flex-direction: column; justify-content: center;
    padding: 6px 9px; border-radius: 8px;
    background: rgba(0,245,255,0.03);
    border: 1px solid rgba(0,245,255,0.15);
    min-height: 54px; overflow: hidden; }}
.mv-time {{ align-items: center; text-align: center; }}
.mv-time-val {{ font-size: 17px; font-weight: 900; color: #f0f5ff;
    font-family: 'JetBrains Mono', monospace; line-height: 1; }}
.mv-league-tag {{ font-size: 8.5px; font-weight: 900; color: #00f5ff;
    text-transform: uppercase;
    background: rgba(0,245,255,0.1);
    border: 1px solid rgba(0,245,255,0.35);
    padding: 2px 8px; border-radius: 100px; margin-top: 4px;
    white-space: nowrap; display: inline-block; }}
.mv-teams {{ flex-direction: row !important;
    align-items: center; justify-content: space-between;
    gap: 6px; padding: 6px 14px; }}
.mv-team {{ display: flex; align-items: center; gap: 9px; min-width: 0; }}
.mv-crest {{ width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, #1a2540, #0f1424);
    border: 1.5px solid rgba(0,245,255,0.45);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 900; color: #00f5ff; flex-shrink: 0; }}
.mv-crest.away {{ color: #b537ff; border-color: rgba(181,55,255,0.45); }}
.mv-team-name {{ font-size: 14px; font-weight: 900; color: #f0f5ff;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.mv-team.left .mv-team-name {{ color: #00f5ff; }}
.mv-team.right .mv-team-name {{ color: #b537ff; }}
.mv-vs {{ font-size: 9px; font-weight: 900; color: #3a4a6a;
    padding: 3px 8px; background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 100px; flex-shrink: 0; }}
.mv-media {{ align-items: center; justify-content: center; text-align: center; }}
.mv-media-vals {{ display: flex; flex-direction: column; gap: 2px;
    font-family: 'JetBrains Mono', monospace; align-items: center; justify-content: center; }}
.mv-media-vals .ht, .mv-media-vals .ft {{ font-size: 14px; font-weight: 900; line-height: 1.15; }}
.mv-media-vals .ht {{ color: #b537ff; }}
.mv-media-vals .ft {{ color: #00f5ff; }}
.mv-bet {{ align-items: center; justify-content: center;
    text-align: center; padding: 6px 8px !important; }}
.mv-bet.green {{ background: linear-gradient(135deg, rgba(0,255,136,0.16), rgba(0,255,136,0.05));
    border-color: rgba(0,255,136,0.55); }}
.mv-bet.red {{ background: linear-gradient(135deg, rgba(255,46,136,0.16), rgba(255,46,136,0.05));
    border-color: rgba(255,46,136,0.55); }}
.mv-bet.cyan {{ background: linear-gradient(135deg, rgba(0,245,255,0.16), rgba(0,245,255,0.05));
    border-color: rgba(0,245,255,0.55); }}
.mv-bet.yellow {{ background: linear-gradient(135deg, rgba(255,214,0,0.16), rgba(255,214,0,0.05));
    border-color: rgba(255,214,0,0.55); }}
.mv-bet-val {{ font-size: 18px; font-weight: 900; line-height: 1.15; text-align: center; }}
.mv-bet-line {{ font-size: 11.5px; font-weight: 900;
    text-transform: uppercase; margin-top: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center; }}
.mv-bet.green .mv-bet-val {{ color: #00ff88; }}
.mv-bet.red   .mv-bet-val {{ color: #ff2e88; }}
.mv-bet.cyan  .mv-bet-val {{ color: #00f5ff; }}
.mv-bet.yellow .mv-bet-val {{ color: #ffd600; }}
.mv-bet.green .mv-bet-line {{ color: #00ff88; }}
.mv-bet.red   .mv-bet-line {{ color: #ff2e88; }}
.mv-bet.cyan  .mv-bet-line {{ color: #00f5ff; }}
.mv-bet.yellow .mv-bet-line {{ color: #ffd600; }}
.mv-over {{ padding: 8px 14px; }}
.mv-over-hdr {{ font-size: 10px; font-weight: 900; color: #00f5ff;
    text-transform: uppercase; letter-spacing: 1px;
    text-align: center; padding-bottom: 4px;
    border-bottom: 1px solid rgba(0,245,255,0.22); margin-bottom: 8px; }}
.mv-over-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
    max-width: 540px; margin: 0 auto; }}
.mv-over-team {{ display: flex; flex-direction: column; gap: 6px; min-width: 0; }}
.mv-over-pname {{ font-size: 15px; font-weight: 900; text-align: center;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    padding-bottom: 6px; border-bottom: 1px dashed rgba(0,245,255,0.2); }}
.mv-over-exp {{ display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 4px;
    margin: 2px 0 6px 0; padding: 10px 12px 8px 12px; border-radius: 10px;
    background: linear-gradient(135deg, rgba(0,245,255,0.12), rgba(181,55,255,0.08));
    border: 1.5px solid rgba(0,245,255,0.5); }}
.mv-over-exp-lbl {{ font-size: 8.5px; color: #00f5ff;
    font-weight: 900; text-transform: uppercase; letter-spacing: 1.4px; }}
.mv-over-exp-main {{ font-family: 'JetBrains Mono', monospace;
    font-size: 30px; font-weight: 900; line-height: 1; letter-spacing: -1.5px; }}
.mv-over-exp-samples {{ display: flex; align-items: center; justify-content: center;
    gap: 8px; width: 100%; margin-top: 3px; padding-top: 6px;
    border-top: 1px dashed rgba(0,245,255,0.2); }}
.mv-over-exp-group {{ display: flex; align-items: center; gap: 4px; flex-shrink: 0; }}
.mv-over-exp-smp {{ font-size: 8.5px; font-weight: 900;
    letter-spacing: 0.4px; padding: 1px 6px; border-radius: 100px;
    flex-shrink: 0; white-space: nowrap; text-transform: uppercase; }}
.mv-over-exp-smp.high {{ color: #00ff88;
    background: rgba(0,255,136,0.15); border: 1px solid rgba(0,255,136,0.45); }}
.mv-over-exp-smp.medium {{ color: #ffd600;
    background: rgba(255,214,0,0.15); border: 1px solid rgba(255,214,0,0.45); }}
.mv-over-exp-smp.low {{ color: #ff2e88;
    background: rgba(255,46,136,0.15); border: 1px solid rgba(255,46,136,0.45); }}
.mv-over-exp-smp.none {{ color: #7a89a8;
    background: rgba(122,137,168,0.12); border: 1px solid rgba(122,137,168,0.3); }}
.mv-over-exp-val-mini {{ font-family: 'JetBrains Mono', monospace;
    font-weight: 900; font-size: 11.5px; }}
.mv-over-exp-sep {{ color: rgba(0,245,255,0.35); font-weight: 900; font-size: 12px; }}
.mv-over-exp-trend {{ font-size: 13px; flex-shrink: 0; }}
.mv-over-stat {{ display: flex; justify-content: space-between;
    align-items: center; gap: 10px; font-size: 12px; padding: 2px 0; }}
.mv-over-lbl {{ font-size: 11px; color: #8b9bb8; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap; }}
.mv-over-pct {{ font-family: 'JetBrains Mono', monospace;
    font-weight: 900; font-size: 15px; flex-shrink: 0; }}
.footer-v2 {{ display: flex; justify-content: space-between; align-items: center;
    padding: 14px 22px; margin-top: 22px;
    background: linear-gradient(135deg, rgba(5,8,20,0.92), rgba(10,15,30,0.92));
    border-top: 1.5px solid rgba(0,245,255,0.35); border-radius: 10px; }}
.footer-v2-left {{ display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 900; color: #f0f5ff;
    letter-spacing: 1.2px; text-transform: uppercase; }}
.footer-v2-accent {{ background: linear-gradient(135deg, #00f5ff, #b537ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.footer-v2-right {{ display: flex; align-items: center; gap: 14px;
    font-size: 10.5px; font-weight: 800; color: #7a89a8;
    letter-spacing: 1.8px; text-transform: uppercase; }}
.footer-v2-right .dot-sep {{ color: #00f5ff; font-size: 14px; }}
.nav-v2 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }}
.pill-actions {{ margin-bottom: 14px; margin-top: 0; }}
</style>"""
    return base


st.markdown(get_css(st.session_state.modo_claro), unsafe_allow_html=True)


# ============================================
# HELPERS
# ============================================
def safe_int(v, default=0):
    try:
        if v is None or v == '': return default
        if isinstance(v, float) and math.isnan(v): return default
        return int(v)
    except (ValueError, TypeError):
        return default


def get_safe_over_line_ft(g):
    if g is None or g == '': return '', ''
    try: g = float(g)
    except: return '', ''
    for m, l, lb in SAFE_LINE_TABLE:
        if g >= m: return l, lb
    return 'Sem Over', 'muito baixa'


def parse_pct(v):
    try: return float(str(v).replace('%', '').strip())
    except: return 0.0


def normalize_league_name(n):
    if not n: return n
    x = n.strip()
    if x in LEAGUE_NAME_MAP: return LEAGUE_NAME_MAP[x]
    for f, s in LEAGUE_NAME_MAP.items():
        if f in x or x in f: return s
    return x


def find_league_key(n, ld):
    if not n: return None
    norm = n.replace('–', '-').replace('—', '-').strip().lower()
    for k in ld.keys():
        kk = k.replace('–', '-').replace('—', '-').strip().lower()
        if kk == norm: return k
    for k in ld.keys():
        kk = k.replace('–', '-').replace('—', '-').strip().lower()
        if norm in kk or kk in norm: return k
    return None


def extract_alias(n):
    if not n: return ''
    s = str(n).strip()
    m = re.search(r'\(([^)]+)\)', s)
    return m.group(1).strip() if m else s


def pbar_color(pct):
    if pct >= 75: return '#00ff88'
    if pct >= 60: return '#ffd600'
    if pct >= 45: return '#ff8c00'
    return '#ff4444'


def team_initial(name):
    s = str(name).strip()
    if not s: return '?'
    parts = re.split(r'[\s_\-]+', s)
    if len(parts) >= 2 and parts[0] and parts[1]:
        return (parts[0][0] + parts[1][0]).upper()
    return s[:2].upper()


def _render_html_safe(html_content: str):
    if hasattr(st, 'html'):
        try:
            st.html(html_content); return
        except Exception:
            pass
    minified = re.sub(r'\n\s*', '', html_content).strip()
    st.markdown(minified, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ═══════════════════════════════════════════════
def render_hero_v2(title="E-SOCCER FIFA", accent="ANALYTICS",
                   right1="IN ALGORITHM",
                   right2_pre="", right2_hl="WE TRUST!",
                   right2_emoji="🧠",
                   tagline="5.000 SIMULAÇÕES POR JOGO. ZERO ACHISMO.",
                   logo="🤖", jersey="👕"):
    badge_content = f'<span class="badge-emoji">{right2_emoji}</span>'
    return (
        '<div class="hero-v2">'
        '<div class="hero-v2-left">'
        f'<div class="hero-v2-logo">{logo}</div>'
        '<div class="hero-v2-title-block">'
        f'<div class="hero-v2-title">{title} <span class="hero-v2-accent">{accent}</span>'
        '<span class="bolt">⚡</span></div>'
        '<div class="hero-v2-tagline">'
        '<span class="hero-v2-at">@FIFAlgorithm</span>'
        '<span class="hero-v2-tag-sep">|</span>'
        f'<span class="hero-v2-tag-text">{tagline}</span>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="hero-v2-right">'
        '<div class="hero-v2-right-text">'
        f'<div class="hero-v2-rl1">{right1}</div>'
        f'<div class="hero-v2-rl2">{right2_pre}<span class="hero-v2-hl">{right2_hl}</span></div>'
        '</div>'
        f'<div class="hero-v2-badge">{badge_content}</div>'
        '</div>'
        '</div>'
    )


def render_info_row_v2(jogos=0, upd_time="--:--", hoje="", online=True,
                       prob_text="Monte Carlo + Dixon-Coles • 5.000 Simulações por jogo"):
    online_html = ('<div class="info-v2-online"><span class="info-v2-dot"></span> ONLINE</div>'
                   if online else '')
    return f"""<div class="info-v2-row">
        <div class="info-v2-card">
            <div class="info-v2-icon">⚽</div>
            <div class="info-v2-content">
                <div class="info-v2-label">JOGOS DISPONÍVEIS</div>
                <div class="info-v2-value">{jogos}</div>
            </div>
        </div>
        <div class="info-v2-card">
            <div class="info-v2-icon">⏰</div>
            <div class="info-v2-content">
                <div class="info-v2-label">ÚLTIMA ATUALIZAÇÃO</div>
                <div class="info-v2-value purple">{upd_time}</div>
                <div class="info-v2-sub">HOJE • {hoje}</div>
            </div>
        </div>
        <div class="info-v2-card">
            <div class="info-v2-icon">🧠</div>
            <div class="info-v2-content" style="flex:1;">
                <div class="info-v2-label" style="color:#00f5ff;">PROBABILIDADES BASEADAS EM</div>
                <div class="info-v2-prob-text">{prob_text}</div>
            </div>
            {online_html}
        </div>
    </div>"""


def render_footer_v2():
    return """<div class="footer-v2">
        <div class="footer-v2-left">
            📊 FOOTBALL ANALYTICS <span class="footer-v2-accent">| FIFAlgorithm</span>
        </div>
        <div class="footer-v2-right">
            ANALISAR <span class="dot-sep">•</span>
            ENTENDER <span class="dot-sep">•</span>
            APOSTAR <span class="dot-sep">•</span>
            EVOLUIR
        </div>
    </div>"""


# ============================================
# ANÁLISE ESTATÍSTICA
# ============================================
def build_league_counters(ad):
    cs = {}
    for ln, ldf in ad.items():
        if ldf is None or ldf.empty: continue
        c = Counter()
        for _, r in ldf.iterrows():
            h = str(r.get('home_team', '')).strip().lower()
            a = str(r.get('away_team', '')).strip().lower()
            if h: c[h] += 1
            if a: c[a] += 1
        cs[ln] = c
    return cs


def compute_jc_jf(df, ad, ld):
    cs = build_league_counters(ad)
    jc_l, jf_l = [], []
    for _, r in df.iterrows():
        lk = find_league_key(r.get('competicao', ''), ld)
        jc = jf = 0
        if lk and lk in cs:
            c = cs[lk]
            jc = c.get(str(r.get('casa', '')).strip().lower(), 0)
            jf = c.get(str(r.get('fora', '')).strip().lower(), 0)
        jc_l.append(jc); jf_l.append(jf)
    return jc_l, jf_l


def get_league_avg(ldf):
    if ldf is None or ldf.empty: return None
    t = ldf['home_score'].sum() + ldf['away_score'].sum()
    n = 2 * len(ldf)
    if n == 0: return None
    af = t / n
    ht = ldf.dropna(subset=['ht_home', 'ht_away'])
    ah = (ht['ht_home'].sum() + ht['ht_away'].sum()) / (2 * len(ht)) if len(ht) > 0 else af * HT_FACTOR
    return {'ataque_ft': af, 'defesa_ft': af, 'ataque_ht': ah, 'defesa_ht': ah}


def get_team_stats(ldf, team):
    if ldf is None or ldf.empty: return None
    tl = str(team).strip().lower()
    if not tl: return None
    tg = ldf[(ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)]
    if tg.empty: return None
    fs, fc, hs, hc = [], [], [], []
    o25 = bt = 0
    gl = []
    for _, g in tg.iterrows():
        is_h = str(g['home_team']).strip().lower() == tl
        a = safe_int(g.get('home_score')); b = safe_int(g.get('away_score'))
        hth = g.get('ht_home'); hta = g.get('ht_away')
        if is_h:
            fs.append(a); fc.append(b)
            if hth is not None and hta is not None:
                hs.append(safe_int(hth)); hc.append(safe_int(hta))
        else:
            fs.append(b); fc.append(a)
            if hth is not None and hta is not None:
                hs.append(safe_int(hta)); hc.append(safe_int(hth))
        tg_t = a + b
        gl.append(tg_t)
        if tg_t > 2.5: o25 += 1
        if a > 0 and b > 0: bt += 1
    nf = len(fs); nh = len(hs)
    if nf == 0: return None
    ak = sum(fs) / nf; df = sum(fc) / nf
    ah = (sum(hs) / nh) if nh > 0 else ak * HT_FACTOR
    dh = (sum(hc) / nh) if nh > 0 else df * HT_FACTOR
    va = float(np.var(fs)) if nf > 1 else 0
    vd = float(np.var(fc)) if nf > 1 else 0
    liga = get_league_avg(ldf)
    if liga:
        k = SHRINKAGE_K
        ak = (ak * nf + liga['ataque_ft'] * k) / (nf + k)
        df = (df * nf + liga['defesa_ft'] * k) / (nf + k)
        ah = (ah * nf + liga['ataque_ht'] * k) / (nf + k)
        dh = (dh * nf + liga['defesa_ht'] * k) / (nf + k)
    media = ak + df
    perfil = 'OFENSIVO' if media >= 4.5 else ('EQUILIBRADO' if media >= 3.5 else 'DEFENSIVO')
    return {'ataque_ft': ak, 'defesa_ft': df, 'ataque_ht': ah, 'defesa_ht': dh,
            'n_ft': nf, 'n_ht': nh, 'var_atk_ft': va, 'var_def_ft': vd,
            'over_25_pct': o25 / nf, 'btts_pct': bt / nf, 'perfil': perfil,
            'total_goals_list': gl, 'media_gols_jogos': media}


def compute_team_over_under(ldf, team):
    if ldf is None or ldf.empty: return {}
    tl = str(team).strip().lower()
    tg = ldf[(ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)]
    if tg.empty: return {}
    gs = []
    for _, g in tg.iterrows():
        is_h = str(g['home_team']).strip().lower() == tl
        gs.append(safe_int(g.get('home_score')) if is_h else safe_int(g.get('away_score')))
    n = len(gs)
    if n == 0: return {}
    return {
        '1.5': sum(1 for g in gs if g >= 2) / n,
        '2.5': sum(1 for g in gs if g >= 3) / n,
        '3.5': sum(1 for g in gs if g >= 4) / n,
        '4.5': sum(1 for g in gs if g >= 5) / n,
        '5.5': sum(1 for g in gs if g >= 6) / n,
    }


def compute_expected_goals(ldf, player_name, opponent_name):
    def _recent(team, n):
        if ldf is None or ldf.empty: return None
        tl = str(team).strip().lower()
        if not tl: return None
        tg = ldf[(ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)].copy()
        if tg.empty: return None
        if 'datetime_obj' in tg.columns and not tg['datetime_obj'].isna().all():
            tg = tg.sort_values('datetime_obj', ascending=False)
        else:
            tg = tg.sort_values('time', ascending=False)
        tg = tg.head(n)
        if tg.empty: return None
        gs, gc = [], []
        for _, g in tg.iterrows():
            is_h = str(g['home_team']).strip().lower() == tl
            a = safe_int(g.get('home_score')); b = safe_int(g.get('away_score'))
            if is_h: gs.append(a); gc.append(b)
            else:    gs.append(b); gc.append(a)
        return {'n': len(gs), 'scored': sum(gs) / len(gs), 'conceded': sum(gc) / len(gc)}

    def _conf(n):
        if n >= 10: return 'high'
        if n >= 5:  return 'medium'
        if n >= 3:  return 'low'
        return 'none'

    p5  = _recent(player_name, 5);   p10 = _recent(player_name, 10)
    o5  = _recent(opponent_name, 5); o10 = _recent(opponent_name, 10)
    if not p5 or not o5: return None
    exp5  = (p5['scored']  + o5['conceded'])  / 2
    exp10 = (p10['scored'] + o10['conceded']) / 2 if (p10 and o10) else exp5
    n5  = min(p5['n'],  o5['n'])
    n10 = min(p10['n'], o10['n']) if (p10 and o10) else n5
    delta = exp5 - exp10
    if delta >= 0.35:    trend, trend_icon, trend_color = 'up',        '📈', '#00ff88'
    elif delta >= 0.15:  trend, trend_icon, trend_color = 'up_lite',   '↗️', '#00ff88'
    elif delta <= -0.35: trend, trend_icon, trend_color = 'down',      '📉', '#ff2e88'
    elif delta <= -0.15: trend, trend_icon, trend_color = 'down_lite', '↘️', '#ff2e88'
    else:                trend, trend_icon, trend_color = 'stable',    '➖', '#7a89a8'
    return {'exp5': exp5, 'exp10': exp10, 'n5': n5, 'n10': n10,
            'conf5': _conf(n5), 'conf10': _conf(n10),
            'trend': trend, 'trend_icon': trend_icon, 'trend_color': trend_color,
            'delta': delta}


def compute_h2h_details(ldf, pa_n, pb_n):
    if ldf is None or ldf.empty: return None
    pa = str(pa_n).strip().lower(); pb = str(pb_n).strip().lower()
    if not pa or not pb: return None
    h2h = ldf[((ldf['home_team'].str.lower() == pa) & (ldf['away_team'].str.lower() == pb)) |
              ((ldf['home_team'].str.lower() == pb) & (ldf['away_team'].str.lower() == pa))].reset_index(drop=True)
    if h2h.empty: return None
    a_f, b_f, a_h, b_h, w = [], [], [], [], []
    o05 = o15 = o25 = o35 = o45 = o55 = bt = 0
    va = vb = emp = 0
    o05h = o15h = o25h = bth = 0
    nh = 0
    for i, (_, g) in enumerate(h2h.iterrows()):
        ww = H2H_RECENCY ** i
        w.append(ww)
        is_h = str(g['home_team']).strip().lower() == pa
        if is_h:
            af = safe_int(g.get('home_score')); bf = safe_int(g.get('away_score'))
            ah = g.get('ht_home'); bh = g.get('ht_away')
        else:
            af = safe_int(g.get('away_score')); bf = safe_int(g.get('home_score'))
            ah = g.get('ht_away'); bh = g.get('ht_home')
        a_f.append(af); b_f.append(bf); a_h.append(ah); b_h.append(bh)
        t = af + bf
        if t > 0.5: o05 += 1
        if t > 1.5: o15 += 1
        if t > 2.5: o25 += 1
        if t > 3.5: o35 += 1
        if t > 4.5: o45 += 1
        if t > 5.5: o55 += 1
        if af > 0 and bf > 0: bt += 1
        if af > bf: va += 1
        elif bf > af: vb += 1
        else: emp += 1
        if ah is not None and bh is not None:
            ah_i = safe_int(ah); bh_i = safe_int(bh); nh += 1
            th = ah_i + bh_i
            if th > 0.5: o05h += 1
            if th > 1.5: o15h += 1
            if th > 2.5: o25h += 1
            if ah_i > 0 and bh_i > 0: bth += 1
    n = len(h2h)
    tw = sum(w)
    la = sum(v * ww for v, ww in zip(a_f, w)) / tw if tw else 0
    lb = sum(v * ww for v, ww in zip(b_f, w)) / tw if tw else 0
    mf = (sum(a_f) + sum(b_f)) / n if n else 0
    perfil = 'OFENSIVO' if mf >= 4.5 else ('EQUILIBRADO' if mf >= 3.0 else 'DEFENSIVO')
    mh = 0
    if nh > 0:
        mh = sum((safe_int(a_h[i]) + safe_int(b_h[i])) for i in range(n)
                 if a_h[i] is not None and b_h[i] is not None) / nh
    return {'n': n, 'lambda_a': la, 'lambda_b': lb, 'media_gols_h2h': mf,
            'media_ft': mf, 'media_ht': mh,
            'over_05': o05 / n if n else 0, 'over_15': o15 / n if n else 0,
            'over_25': o25 / n if n else 0, 'over_35': o35 / n if n else 0,
            'over_45': o45 / n if n else 0, 'over_55': o55 / n if n else 0,
            'btts': bt / n if n else 0,
            'over_05_ht': o05h / nh if nh else 0, 'over_15_ht': o15h / nh if nh else 0,
            'over_25_ht': o25h / nh if nh else 0, 'btts_ht': bth / nh if nh else 0,
            'vitorias_a': va, 'vitorias_b': vb, 'empates': emp, 'perfil_h2h': perfil}


def estimate_lambdas(ldf, casa, fora):
    sc = get_team_stats(ldf, casa); sf = get_team_stats(ldf, fora)
    if not sc or not sf: return None
    if sc['n_ft'] == 0 or sf['n_ft'] == 0: return None
    lcf_f = (sc['ataque_ft'] + sf['defesa_ft']) / 2
    lff_f = (sf['ataque_ft'] + sc['defesa_ft']) / 2
    lch_f = (sc['ataque_ht'] + sf['defesa_ht']) / 2
    lfh_f = (sf['ataque_ht'] + sc['defesa_ht']) / 2
    h2h = compute_h2h_details(ldf, casa, fora)
    nh = 0
    if h2h:
        nh = h2h['n']
        ph = min(nh / H2H_FULL_TRUST_N, H2H_MAX_WEIGHT)
        pf = 1 - ph
        lcf = ph * h2h['lambda_a'] + pf * lcf_f
        lff = ph * h2h['lambda_b'] + pf * lff_f
        lch, lfh = lch_f, lfh_f
    else:
        lcf, lff, lch, lfh = lcf_f, lff_f, lch_f, lfh_f
    av = (sc['var_atk_ft'] + sf['var_atk_ft'] + sc['var_def_ft'] + sf['var_def_ft']) / 4
    ns = min(nh, 8) / 8 * 30 + min(min(sc['n_ft'], sf['n_ft']), 15) / 15 * 30
    cs = max(0, 1 - min(av / 4.0, 1)) * 40
    conf = int(min(ns + cs, 100))
    em = "🟢" if conf >= 70 else ("🟡" if conf >= 45 else "🔴")
    return {'lam_casa_ft': lcf, 'lam_fora_ft': lff, 'lam_casa_ht': lch, 'lam_fora_ht': lfh,
            'conf_score': conf, 'conf_emoji': em}


def poisson_pmf(lam, mx):
    ks = np.arange(mx + 1)
    f = np.array([math.factorial(int(k)) for k in ks], dtype=float)
    lam = max(lam, 1e-9)
    return np.exp(-lam) * np.power(lam, ks) / f


def dc_tau(i, j, lam, mu, rho=DC_RHO):
    if i == 0 and j == 0: return 1 - lam * mu * rho
    if i == 0 and j == 1: return 1 + lam * rho
    if i == 1 and j == 0: return 1 + mu * rho
    if i == 1 and j == 1: return 1 - rho
    return 1.0


def build_dc(lam, mu, mx=DC_MAX_GOALS):
    pl = poisson_pmf(lam, mx); pm = poisson_pmf(mu, mx)
    m = np.outer(pl, pm)
    for i in range(min(2, mx + 1)):
        for j in range(min(2, mx + 1)):
            m[i, j] *= dc_tau(i, j, lam, mu)
    m = np.clip(m, 0, None)
    s = m.sum()
    if s > 0: m /= s
    return m


def sample_dc(lam, mu, ns, rng, mx=DC_MAX_GOALS):
    m = build_dc(lam, mu, mx)
    flat = m.flatten()
    idx = rng.choice(len(flat), size=ns, p=flat)
    return idx // (mx + 1), idx % (mx + 1)


def compute_1x2_probs(ldf, casa, fora):
    lam = estimate_lambdas(ldf, casa, fora)
    if not lam: return (0.33, 0.33, 0.34)
    lcf = lam['lam_casa_ft']; lff = lam['lam_fora_ft']
    if lcf <= 0 or lff <= 0: return (0.33, 0.33, 0.34)
    m = build_dc(lcf, lff, mx=8)
    p_home = p_draw = p_away = 0
    for i in range(9):
        for j in range(9):
            if i > j: p_home += m[i, j]
            elif i == j: p_draw += m[i, j]
            else: p_away += m[i, j]
    return (p_home, p_draw, p_away)


def monte_carlo(df, ad, ld, ns=N_SIMULATIONS, seed=42):
    rng = np.random.default_rng(seed)
    out = {c: [] for c in EXTRA_COLUMNS}
    for idx, r in df.iterrows():
        lk = find_league_key(r.get('competicao', ''), ld)
        casa = str(r.get('casa', '')).strip().lower()
        fora = str(r.get('fora', '')).strip().lower()
        res = {c: '' for c in EXTRA_COLUMNS}
        if lk and lk in ad:
            ldf = ad[lk]
            try:
                lam = estimate_lambdas(ldf, casa, fora)
                if lam:
                    lcf, lff = lam['lam_casa_ft'], lam['lam_fora_ft']
                    lch, lfh = lam['lam_casa_ht'], lam['lam_fora_ht']
                    if lcf > 0 and lff > 0:
                        gc, gf = sample_dc(lcf, lff, ns, rng)
                        t = gc + gf
                        res['xG Casa'] = round(float(lcf), 2)
                        res['xG Fora'] = round(float(lff), 2)
                        gm = round(float(t.mean()), 2)
                        res['Gols FT'] = gm
                        res['Over 0.5 FT'] = f"{(t > 0.5).mean() * 100:.1f}%"
                        res['Over 1.5 FT'] = f"{(t > 1.5).mean() * 100:.1f}%"
                        res['Over 2.5 FT'] = f"{(t > 2.5).mean() * 100:.1f}%"
                        res['Over 3.5 FT'] = f"{(t > 3.5).mean() * 100:.1f}%"
                        res['Over 4.5 FT'] = f"{(t > 4.5).mean() * 100:.1f}%"
                        res['Over 5.5 FT'] = f"{(t > 5.5).mean() * 100:.1f}%"
                        res['BTTS FT'] = f"{((gc > 0) & (gf > 0)).mean() * 100:.1f}%"
                        res['O1.5 Jogador'] = f"{((gc >= 2) | (gf >= 2)).mean() * 100:.1f}%"
                        res['O2.5 Jogador'] = f"{((gc >= 3) | (gf >= 3)).mean() * 100:.1f}%"
                        ln, _ = get_safe_over_line_ft(gm)
                        res['Linha Seg FT'] = ln
                        p_h, p_d, p_a = compute_1x2_probs(ldf, casa, fora)
                        res['Prob Casa'] = f"{p_h * 100:.0f}%"
                        res['Prob Empate'] = f"{p_d * 100:.0f}%"
                        res['Prob Fora'] = f"{p_a * 100:.0f}%"
                    if lch and lfh and lch > 0 and lfh > 0:
                        gch, gfh = sample_dc(lch, lfh, ns, rng)
                        th = gch + gfh
                        p_o25ht = (th > 2.5).mean() * 100
                        p_o15ht = (th > 1.5).mean() * 100
                        p_o05ht = (th > 0.5).mean() * 100
                        res['Gols HT'] = round(float(th.mean()), 2)
                        res['Over 0.5 HT'] = f"{p_o05ht:.1f}%"
                        res['Over 1.5 HT'] = f"{p_o15ht:.1f}%"
                        res['Over 2.5 HT'] = f"{p_o25ht:.1f}%"
                        res['BTTS HT'] = f"{((gch > 0) & (gfh > 0)).mean() * 100:.1f}%"
                        if p_o25ht >= 65:
                            res['Rec HT'] = 'Over 2.5 HT'; res['Prob Rec HT'] = f"{p_o25ht:.0f}%"; res['O2.5 HT?'] = '✅'
                        elif p_o15ht >= 75:
                            res['Rec HT'] = 'Over 1.5 HT'; res['Prob Rec HT'] = f"{p_o15ht:.0f}%"; res['O2.5 HT?'] = '❌'
                        elif p_o05ht >= 85:
                            res['Rec HT'] = 'Over 0.5 HT'; res['Prob Rec HT'] = f"{p_o05ht:.0f}%"; res['O2.5 HT?'] = '❌'
                        else:
                            res['Rec HT'] = 'Evitar HT'; res['Prob Rec HT'] = '-'; res['O2.5 HT?'] = '❌'
                    res['Conf'] = f"{lam['conf_emoji']} {lam['conf_score']}"
            except Exception:
                pass
        for c in EXTRA_COLUMNS: out[c].append(res[c])
    return out


@st.cache_data(ttl=300, show_spinner=False, max_entries=8)
def monte_carlo_cached(df: pd.DataFrame, ad: dict, ns: int = N_SIMULATIONS, seed: int = 42):
    return monte_carlo(df, ad, LEAGUES, ns=ns, seed=seed)


# ============================================
# SCRAPER COM PLAYWRIGHT (passa Cloudflare)
# ============================================
class EFootballScraper:
    def __init__(self):
        self.base_url = "https://24live.com/api"

    def _fetch_via_playwright(self, url: str, params: dict, timeout: int = 30):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None

        import urllib.parse
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox',
                          '--disable-dev-shm-usage', '--disable-gpu', '--single-process']
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/131.0.0.0 Safari/537.36',
                    locale='pt-BR',
                    viewport={'width': 1920, 'height': 1080},
                )
                page = context.new_page()
                page.goto('https://24live.com/pt/', wait_until='domcontentloaded', timeout=timeout * 1000)
                page.wait_for_timeout(3000)
                page.goto(full_url, wait_until='domcontentloaded', timeout=timeout * 1000)
                page.wait_for_timeout(1500)
                text = page.content()
                browser.close()

                from bs4 import BeautifulSoup as _BS
                soup = _BS(text, 'html.parser')
                body = soup.find('pre') or soup.find('body')
                raw = body.get_text() if body else text
                try:
                    return json.loads(raw)
                except Exception:
                    m = re.search(r'(\[.*\]|\{.*\})', raw, re.DOTALL)
                    if m:
                        try: return json.loads(m.group(1))
                        except: pass
                    return None
        except Exception as e:
            st.session_state['_fetch_errors'].append(f"Playwright: {type(e).__name__}: {e}")
            return None

    def get_league_matches(self, sid, max_retries=2, timeout=30):
        url = f"{self.base_url}/match-list-data/105"
        now = datetime.now()
        st_ = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        en = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
        params = {
            'lang': 'pt', 'type': 'all', 'subtournamentIds': str(sid),
            'sort': 'alpha', 'short': 0,
            'from': st_.strftime('%Y-%m-%d %H:%M:%S'),
            'to': en.strftime('%Y-%m-%d %H:%M:%S'),
            'defaultSubtournamentLimit': 1000, 'orderBy': 'desc'
        }

        # Tentativa 1: cloudscraper
        try:
            import cloudscraper
            sess = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            sess.headers.update({
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://24live.com/pt/',
                'Origin': 'https://24live.com',
            })
            r = sess.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        # Tentativa 2: Playwright
        result = self._fetch_via_playwright(url, params, timeout=timeout)
        if result is not None:
            return result

        st.session_state['_fetch_errors'].append(f"{sid}: Todas as tentativas falharam")
        return []

    def extract(self, data):
        out = []
        today = datetime.now().strftime('%d/%m')
        total = ended = mt = 0
        sm = []
        for m in data:
            total += 1
            cs = m.get('code_state', 'unknown')
            if cs != 'ended': continue
            ended += 1
            p = m.get('participants', [])
            h = next((x for x in p if x.get('type') == 'home_team'), {})
            a = next((x for x in p if x.get('type') == 'away_team'), {})
            sc = m.get('score', {})
            periods = sc.get('periods', [])
            hth = hta = None
            for per in periods:
                if per.get('period') == 1:
                    hth = per.get('home_team'); hta = per.get('away_team'); break
            hth = safe_int(hth, None) if hth is not None else None
            hta = safe_int(hta, None) if hta is not None else None
            sd = m.get('start_date', '')
            ds = ts = ''; dl = None
            if sd:
                try:
                    x = sd[:-1] if sd.endswith('Z') else sd
                    x = x.replace('+00:00', '')
                    dt = datetime.fromisoformat(x)
                    dl = dt - timedelta(hours=3)
                    ds = dl.strftime('%d/%m'); ts = dl.strftime('%H:%M')
                except:
                    ds = sd[:10] if len(sd) >= 10 else ''
                    ts = sd[11:16] if len(sd) >= 16 else ''
            if len(sm) < 8: sm.append(f"{ds} {ts} ({cs})")
            if ds != today: continue
            mt += 1
            out.append({'id': m.get('id'), 'status': cs, 'date': ds, 'time': ts,
                        'start_date': sd, 'datetime_obj': dl,
                        'home_team': extract_alias(h.get('name', 'N/A')),
                        'away_team': extract_alias(a.get('name', 'N/A')),
                        'home_team_full': h.get('name', 'N/A'),
                        'away_team_full': a.get('name', 'N/A'),
                        'home_score': safe_int(sc.get('home_team')),
                        'away_score': safe_int(sc.get('away_team')),
                        'ht_home': hth, 'ht_away': hta,
                        'winner': m.get('winner', 0),
                        'tournament': m.get('tournament_name', 'N/A'),
                        'category': m.get('category_name', 'N/A')})
        self.last_debug = {'total': total, 'ended': ended, 'matched_today': mt,
                           'today_str': today, 'sample_dates': sm}
        return out


def test_24live_connectivity():
    try:
        import cloudscraper
        scraper_test = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        r = scraper_test.get("https://24live.com/api/match-list-data/105", timeout=15, params={
            'lang': 'pt', 'type': 'all', 'subtournamentIds': '179369',
            'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'to': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
        }, headers={'Accept': 'application/json', 'Referer': 'https://24live.com/pt/'})
        return r.status_code == 200, f"HTTP {r.status_code} · {len(r.text)} bytes"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def scrape_aceodds(max_retries=ACEODDS_MAX_RETRIES, timeout=ACEODDS_TIMEOUT):
    url = "https://www.aceodds.com/pt/bet365-transmissao-ao-vivo/futebol.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8', 'Upgrade-Insecure-Requests': '1',
    }
    if 'aceodds_session' not in st.session_state:
        sess = requests.Session(); sess.headers.update(headers)
        st.session_state['aceodds_session'] = sess
    sess = st.session_state['aceodds_session']
    r = None
    for attempt in range(max_retries):
        try:
            with st.spinner(f"Conectando AceOdds... ({attempt + 1}/{max_retries})"):
                r = sess.get(url, timeout=timeout); r.raise_for_status(); break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt); continue
            else:
                return st.session_state.get('aceodds_games', [])
        except Exception:
            return st.session_state.get('aceodds_games', [])
    if r is None: return st.session_state.get('aceodds_games', [])
    try:
        soup = BeautifulSoup(r.text, 'html.parser')
        jogos = []
        for row in soup.find_all('tr'):
            rt = row.get_text(" ", strip=True)
            if 'E-Soccer' not in rt: continue
            cells = row.find_all('td')
            if len(cells) < 3: continue
            ct = [c.get_text(" ", strip=True) for c in cells]
            hora = casa = fora = comp = status = ''
            for c in ct:
                cc = c.strip()
                if not cc: continue
                if not hora and re.match(r'^\d{1,2}:\d{2}$', cc): hora = cc; continue
                if 'E-Soccer' in cc: comp = cc; continue
                if not casa and (' x ' in cc or ' vs ' in cc):
                    sep = ' x ' if ' x ' in cc else ' vs '
                    parts = cc.split(sep, 1)
                    casa = parts[0].strip()
                    fora = parts[1].strip() if len(parts) > 1 else ''
                    continue
                cu = cc.upper()
                if 'AO VIVO' in cu or 'LIVE' in cu or 'AGENDADO' in cu: status = cc; continue
            if not casa and len(ct) > 1: casa = ct[1]
            if not fora and len(ct) > 2: fora = ct[2]
            casa = re.sub(r'^(Ao Vivo Agora|Ao Vivo|Agendado)\s*', '', casa, flags=re.IGNORECASE).strip()
            fora = re.sub(r'^(Ao Vivo Agora|Ao Vivo|Agendado)\s*', '', fora, flags=re.IGNORECASE).strip()
            if casa and ' x ' in casa and not fora:
                p = casa.split(' x ', 1); casa = p[0].strip(); fora = p[1].strip()
            su = (status + ' ' + rt).upper()
            is_live = 'AO VIVO' in su or 'LIVE' in su
            ca = extract_alias(casa); fa = extract_alias(fora)
            if ca or fa:
                jogos.append({'hora': hora, 'casa': ca, 'fora': fa,
                              'casa_full': casa, 'fora_full': fora,
                              'competicao': comp, 'status': status, 'is_live': is_live})
        return jogos
    except Exception as e:
        st.error(f"Erro AceOdds: {e}")
        return st.session_state.get('aceodds_games', [])


# ============================================
# SOM / ALERTA
# ============================================
def play_alert_sound():
    try:
        html = """<script>
try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    function beep(f, d, w) {
      const o = ctx.createOscillator(); const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = f; o.type = 'sine';
      g.gain.setValueAtTime(0.001, ctx.currentTime + w);
      g.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + w + 0.02);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + w + d);
      o.start(ctx.currentTime + w); o.stop(ctx.currentTime + w + d + 0.05);
    }
    beep(880, 0.15, 0); beep(1320, 0.15, 0.2); beep(1760, 0.25, 0.4);
} catch(e) {}
</script>"""
        b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
        try: st.iframe(f"data:text/html;base64,{b64}", height=1)
        except AttributeError: components.html(html, height=0)
    except Exception:
        pass


def check_oportunidades(df):
    if df is None or df.empty: return []
    opps = df[df['O2.5 HT?'].eq('✅') & df['Conf'].astype(str).str.contains('🟢', na=False)]
    novas = []
    for _, r in opps.iterrows():
        key = f"{r.get('hora', '')}|{r.get('casa', '')}|{r.get('fora', '')}"
        if key not in st.session_state.ultima_oportunidade:
            novas.append(r); st.session_state.ultima_oportunidade.add(key)
    return novas


def emitir_alerta(novas):
    if not novas: return
    if st.session_state.notif_alerta:
        for r in novas[:5]:
            st.toast(f"🎯 **{r['casa']} × {r['fora']}**\n\n"
                     f"🟢 Alta confiança + Over 2.5 HT │ {r.get('Over 2.5 HT', '')}", icon="🚨")
    if st.session_state.som_ativo: play_alert_sound()


# ============================================
# RENDER HELPERS
# ============================================
def render_progress_row(label, pct):
    color = pbar_color(pct * 100)
    return f'''<div class="prog-row">
        <div class="prog-lbl">{label}</div>
        <div class="prog-val" style="color:{color};">{pct * 100:.1f}%</div>
        <div class="pbar"><div style="width:{min(pct * 100, 100)}%; background:{color};"></div></div>
    </div>'''


def render_card_header():
    return (
        '<div class="match-v2-header">'
        '<div class="mvh-cell">Hora/Liga</div>'
        '<div class="mvh-cell">Confronto</div>'
        '<div class="mvh-cell">📊 Média</div>'
        '<div class="mvh-cell">🎯 Apostar HT</div>'
        '<div class="mvh-cell">🎯 Apostar FT</div>'
        '<div class="mvh-cell">⭐ Over Players</div>'
        '</div>'
    )


def render_card_row_v2(row, casa_raw, fora_raw, ldf=None, perfil_a=None, perfil_b=None):
    hora = str(row.get('hora', '--:--'))
    liga_full = str(row.get('competicao', '')).upper()
    liga = liga_full.replace('E-SOCCER - ', '').replace(' - ', ' ').replace('E-SOCCER', '').strip()

    try: gols_ft = float(row.get('Gols FT', 0) or 0)
    except: gols_ft = 0.0
    try: gols_ht = float(row.get('Gols HT', 0) or 0)
    except: gols_ht = 0.0

    rec_ht = row.get('Rec HT', 'Evitar HT')
    prob_rec_ht = row.get('Prob Rec HT', '-')

    if 'Over 2.5' in rec_ht:
        ht_cls, ht_lbl, ht_line = 'green', prob_rec_ht, 'OVER 2.5 HT'
    elif 'Over 1.5' in rec_ht:
        ht_cls, ht_lbl, ht_line = 'yellow', prob_rec_ht, 'OVER 1.5 HT'
    elif 'Over 0.5' in rec_ht:
        ht_cls, ht_lbl, ht_line = 'cyan', prob_rec_ht, 'OVER 0.5 HT'
    else:
        ht_cls, ht_lbl, ht_line = 'red', '—', 'EVITAR HT'

    linha_seg = row.get('Linha Seg FT', '') or '—'
    linha_atende = linha_seg not in ('—', 'Sem Over', '')
    ft_cls, ft_lbl = ('cyan', linha_seg) if linha_atende else ('red', 'SEM LINHA')

    ou_a = compute_team_over_under(ldf, casa_raw.lower()) if ldf is not None else {}
    ou_b = compute_team_over_under(ldf, fora_raw.lower()) if ldf is not None else {}
    p_a_15 = ou_a.get('1.5', 0) * 100; p_a_25 = ou_a.get('2.5', 0) * 100
    p_a_35 = ou_a.get('3.5', 0) * 100
    p_b_15 = ou_b.get('1.5', 0) * 100; p_b_25 = ou_b.get('2.5', 0) * 100
    p_b_35 = ou_b.get('3.5', 0) * 100

    exp_a = compute_expected_goals(ldf, casa_raw, fora_raw) if ldf is not None else None
    exp_b = compute_expected_goals(ldf, fora_raw, casa_raw) if ldf is not None else None

    def c_pct(p):
        if p >= 60: return '#00ff88'
        if p >= 40: return '#ffd600'
        return '#ff8c00'

    def c_exp(v):
        if v >= 3.5: return '#00ff88'
        if v >= 2.5: return '#ffd600'
        if v >= 1.5: return '#ff8c00'
        return '#ff2e88'

    def exp_html_block(exp_data):
        if not exp_data:
            return ('<div class="mv-over-exp">'
                    '<span class="mv-over-exp-lbl">Gols Esperados</span>'
                    '<span class="mv-over-exp-main" style="color:#7a89a8;">—</span>'
                    '</div>')
        e5, e10 = exp_data['exp5'], exp_data['exp10']
        c5, c10 = c_exp(e5), c_exp(e10)
        main_color = c_exp(e5)
        return (
            '<div class="mv-over-exp">'
            '<span class="mv-over-exp-lbl">Gols Esperados</span>'
            f'<span class="mv-over-exp-main" style="color:{main_color};">{e5:.2f}</span>'
            '<div class="mv-over-exp-samples">'
            '<span class="mv-over-exp-group">'
            f'<span class="mv-over-exp-smp {exp_data["conf5"]}">{exp_data["n5"]} JG</span>'
            f'<span class="mv-over-exp-val-mini" style="color:{c5};">{e5:.2f}</span>'
            '</span><span class="mv-over-exp-sep">│</span>'
            '<span class="mv-over-exp-group">'
            f'<span class="mv-over-exp-smp {exp_data["conf10"]}">{exp_data["n10"]} JG</span>'
            f'<span class="mv-over-exp-val-mini" style="color:{c10};">{e10:.2f}</span>'
            '</span>'
            f'<span class="mv-over-exp-trend" style="color:{exp_data["trend_color"]};">'
            f'{exp_data["trend_icon"]}</span></div></div>'
        )

    a_ini = team_initial(casa_raw); b_ini = team_initial(fora_raw)

    def over_team_block(name, p15, p25, p35, color, exp_data):
        return f'''<div class="mv-over-team">
            <div class="mv-over-pname" style="color:{color};">{name[:16]}</div>
            {exp_html_block(exp_data)}
            <div class="mv-over-stat"><span class="mv-over-lbl">Marcar 1.5</span>
                <span class="mv-over-pct" style="color:{c_pct(p15)};">{p15:.0f}%</span></div>
            <div class="mv-over-stat"><span class="mv-over-lbl">Marcar 2.5</span>
                <span class="mv-over-pct" style="color:{c_pct(p25)};">{p25:.0f}%</span></div>
            <div class="mv-over-stat"><span class="mv-over-lbl">Marcar 3.5</span>
                <span class="mv-over-pct" style="color:{c_pct(p35)};">{p35:.0f}%</span></div>
        </div>'''

    return (
        '<div class="match-v2-row">'
        f'<div class="mv-box mv-time"><div class="mv-time-val">{hora}</div>'
        f'<div class="mv-league-tag">{liga[:22]}</div></div>'
        '<div class="mv-box mv-teams">'
        f'<div class="mv-team left"><div class="mv-crest">{a_ini}</div>'
        f'<span class="mv-team-name">{casa_raw[:18]}</span></div>'
        '<span class="mv-vs">VS</span>'
        f'<div class="mv-team right"><span class="mv-team-name">{fora_raw[:18]}</span>'
        f'<div class="mv-crest away">{b_ini}</div></div>'
        '</div>'
        f'<div class="mv-box mv-media"><div class="mv-media-vals">'
        f'<span class="ht">HT {gols_ht:.2f}</span>'
        f'<span class="ft">FT {gols_ft:.2f}</span></div></div>'
        f'<div class="mv-box mv-bet {ht_cls}">'
        f'<div class="mv-bet-val">{ht_lbl}</div>'
        f'<div class="mv-bet-line">{ht_line}</div></div>'
        f'<div class="mv-box mv-bet {ft_cls}">'
        f'<div class="mv-bet-val">{ft_lbl}</div></div>'
        f'<div class="mv-box mv-over">'
        f'<div class="mv-over-hdr">⭐ OVER INDIVIDUAL</div>'
        f'<div class="mv-over-cols">'
        f'{over_team_block(casa_raw, p_a_15, p_a_25, p_a_35, "#00ff88", exp_a)}'
        f'{over_team_block(fora_raw, p_b_15, p_b_25, p_b_35, "#00f5ff", exp_b)}'
        f'</div></div></div>'
    )


def render_h2h_comparison(casa_raw, fora_raw, ldf, hora='--:--', liga=''):
    if ldf is None or ldf.empty:
        return '<p style="color:#7a89a8; padding:12px;">Sem dados H2H.</p>'

    def get_last_10(team_name):
        tl = team_name.strip().lower()
        mask = (ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)
        games = ldf[mask].copy()
        if games.empty: return None
        if 'datetime_obj' in games.columns and not games['datetime_obj'].isna().all():
            games = games.sort_values('datetime_obj', ascending=False)
        else:
            games = games.sort_values('time', ascending=False)
        games = games.head(10)
        gm, gs, ht, ft, form = [], [], [], [], []
        pts = 0
        for _, g in games.iterrows():
            is_h = str(g['home_team']).strip().lower() == tl
            a = safe_int(g.get('home_score')); b = safe_int(g.get('away_score'))
            hth_r = g.get('ht_home'); hta_r = g.get('ht_away')
            hth = safe_int(hth_r) if hth_r is not None and not (isinstance(hth_r, float) and math.isnan(hth_r)) else None
            hta = safe_int(hta_r) if hta_r is not None and not (isinstance(hta_r, float) and math.isnan(hta_r)) else None
            my = a if is_h else b; opp = b if is_h else a
            gm.append(str(my)); gs.append(str(opp))
            if hth is not None and hta is not None:
                ht_my = hth if is_h else hta; ht_opp = hta if is_h else hth
                ht.append(f"{ht_my}-{ht_opp}")
            else: ht.append("—")
            ft.append(f"{my}-{opp}")
            if my > opp: form.append('V'); pts += 3
            elif my < opp: form.append('D')
            else: form.append('E'); pts += 1
        n = len(gm)
        ht_valid = [x for x in ht if x != "—"]
        return {'gm': gm, 'gs': gs, 'ht': ht, 'ft': ft, 'form': form, 'n': n,
                'avg_gm': sum(int(x) for x in gm) / n if n else 0,
                'avg_gs': sum(int(x) for x in gs) / n if n else 0,
                'avg_ht': (sum(sum(int(i) for i in x.split('-')) for x in ht_valid) / len(ht_valid)) if ht_valid else 0,
                'avg_ft': sum(sum(int(i) for i in x.split('-')) for x in ft) / n if n else 0,
                'ppj': pts / n if n else 0}

    sa = get_last_10(casa_raw); sb = get_last_10(fora_raw)
    if not sa or not sb:
        return '<p style="color:#7a89a8; padding:12px;">Sem dados suficientes.</p>'

    def form_dots(f):
        html = ''
        for x in f:
            if x == 'V': bg, fc = '#00ff88', '#05070f'
            elif x == 'E': bg, fc = '#ffd600', '#05070f'
            else: bg, fc = '#ff2e88', '#ffffff'
            html += (f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                     f'width:20px;height:20px;border-radius:50%;background:{bg};color:{fc};'
                     f'font-size:10px;font-weight:900;font-family:\'JetBrains Mono\',monospace;'
                     f'margin:0 2px;line-height:1;flex-shrink:0;">{x}</span>')
        return html

    def seq(items, mode='goals'):
        html = ''
        for it in items:
            if mode == 'goals':
                try: hl = 'highlight' if int(it) > 0 else ''
                except: hl = ''
            elif mode == 'ht':
                if it == "—": hl = ''
                else:
                    try: hl = 'ht-hl' if sum(int(i) for i in it.split('-')) > 0 else ''
                    except: hl = ''
            else: hl = 'highlight'
            html += f'<span class="h2h-seq-item {hl}">{it}</span>'
        return html

    def ppj_color(p):
        if p >= 2.5: return '#00ff88'
        if p >= 2.0: return '#00f5ff'
        if p >= 1.5: return '#ffd600'
        if p >= 1.0: return '#ff8c00'
        return '#ff2e88'

    return f"""<div class="h2h-card">
        <div class="h2h-header">
            <div class="h2h-team">
                <div class="h2h-team-name">🛡️ {casa_raw}</div>
                <div class="h2h-team-form">{form_dots(sa['form'])}</div>
            </div>
            <div class="h2h-match-info">
                <div class="vs">VS</div>
                <div class="league">{hora} · ÚLTIMOS 10</div>
            </div>
            <div class="h2h-team right">
                <div class="h2h-team-name">{fora_raw} 🛡️</div>
                <div class="h2h-team-form">{form_dots(sb['form'])}</div>
            </div>
        </div>
        <div class="h2h-table">
            <div class="h2h-col">
                <div class="h2h-row"><div class="h2h-row-label">Gols Marcados</div>
                    <div class="h2h-row-seq">{seq(sa['gm'], 'goals')}</div>
                    <div class="h2h-row-avg">{sa['avg_gm']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Gols Sofridos</div>
                    <div class="h2h-row-seq">{seq(sa['gs'], 'goals')}</div>
                    <div class="h2h-row-avg">{sa['avg_gs']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Jogos HT</div>
                    <div class="h2h-row-seq">{seq(sa['ht'], 'ht')}</div>
                    <div class="h2h-row-avg ht">{sa['avg_ht']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Jogos FT</div>
                    <div class="h2h-row-seq">{seq(sa['ft'], 'ft')}</div>
                    <div class="h2h-row-avg ft">{sa['avg_ft']:.1f}</div></div>
            </div>
            <div class="h2h-col">
                <div class="h2h-row"><div class="h2h-row-label">Gols Marcados</div>
                    <div class="h2h-row-seq">{seq(sb['gm'], 'goals')}</div>
                    <div class="h2h-row-avg">{sb['avg_gm']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Gols Sofridos</div>
                    <div class="h2h-row-seq">{seq(sb['gs'], 'goals')}</div>
                    <div class="h2h-row-avg">{sb['avg_gs']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Jogos HT</div>
                    <div class="h2h-row-seq">{seq(sb['ht'], 'ht')}</div>
                    <div class="h2h-row-avg ht">{sb['avg_ht']:.1f}</div></div>
                <div class="h2h-row"><div class="h2h-row-label">Jogos FT</div>
                    <div class="h2h-row-seq">{seq(sb['ft'], 'ft')}</div>
                    <div class="h2h-row-avg ft">{sb['avg_ft']:.1f}</div></div>
            </div>
        </div>
    </div>"""


def render_match_card(row, ad, ld, idx=0):
    lk = find_league_key(row.get('competicao', ''), ld)
    casa_raw = str(row.get('casa', '')); fora_raw = str(row.get('fora', ''))
    casa = casa_raw.strip().lower(); fora = fora_raw.strip().lower()
    if not lk or lk not in ad:
        st.info("Sem dados da liga."); return
    ldf = ad[lk]

    st.markdown('<div class="section-label">📊 OVER/UNDER PARTIDA</div>', unsafe_allow_html=True)
    ou_parts = []
    for line in ['0.5', '1.5', '2.5']:
        col = f'Over {line} HT'
        if col in row and row[col]:
            try: pct = parse_pct(row[col]) / 100
            except: continue
            ou_parts.append(render_progress_row(f'{line} HT', pct))
    for line in ['0.5', '1.5', '2.5', '3.5', '4.5', '5.5']:
        col = f'Over {line} FT'
        if col in row and row[col]:
            try: pct = parse_pct(row[col]) / 100
            except: continue
            ou_parts.append(render_progress_row(f'{line} FT', pct))
    if ou_parts:
        st.markdown(f'<div style="background: rgba(0,0,0,0.4); padding: 10px 16px; border-radius:10px; border:1px solid rgba(0,245,255,0.15);">{"".join(ou_parts)}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">🎯 OVER INDIVIDUAL</div>', unsafe_allow_html=True)
    ou_a = compute_team_over_under(ldf, casa); ou_b = compute_team_over_under(ldf, fora)
    c1, c2 = st.columns(2)
    for col, team_name, ou_data, cor in [(c1, casa_raw, ou_a, '#00ff88'), (c2, fora_raw, ou_b, '#00f5ff')]:
        with col:
            if not ou_data:
                st.markdown(f'<div style="font-size:12.5px; color:#7a89a8; padding:10px;">Sem dados p/ {team_name[:15]}</div>', unsafe_allow_html=True)
                continue
            rows_html = ''
            for line, pct in ou_data.items():
                rows_html += render_progress_row(line, pct)
            st.markdown(f'''<div style="background: rgba(0,0,0,0.4); padding: 10px 14px; border-radius:10px; border:1px solid rgba(0,245,255,0.15);">
                <div style="font-size:13px; font-weight:800; color:{cor}; margin-bottom:8px;">{team_name[:20]}</div>
                {rows_html}</div>''', unsafe_allow_html=True)


# ============================================
# INSIGHTS PLAYERS
# ============================================
def _compute_window_stats(last_n, tl):
    if last_n.empty: return None
    nf = len(last_n)
    goals_for, goals_against, ht_goals, ft_goals = [], [], [], []
    form = []; over25 = btts = o15ht = o25ht = 0; points = 0
    for _, g in last_n.iterrows():
        is_h = str(g['home_team']).strip().lower() == tl
        a = safe_int(g.get('home_score')); b = safe_int(g.get('away_score'))
        hth_r = g.get('ht_home'); hta_r = g.get('ht_away')
        hth = safe_int(hth_r) if hth_r is not None and not (isinstance(hth_r, float) and math.isnan(hth_r)) else None
        hta = safe_int(hta_r) if hta_r is not None and not (isinstance(hta_r, float) and math.isnan(hta_r)) else None
        my = a if is_h else b; opp = b if is_h else a
        total = a + b
        ht_total = (hth + hta) if (hth is not None and hta is not None) else None
        goals_for.append(my); goals_against.append(opp); ft_goals.append(total)
        if ht_total is not None: ht_goals.append(ht_total)
        if my > opp: form.append('V'); points += 3
        elif my < opp: form.append('D')
        else: form.append('E'); points += 1
        if total > 2.5: over25 += 1
        if a > 0 and b > 0: btts += 1
        if ht_total is not None:
            if ht_total > 1.5: o15ht += 1
            if ht_total > 2.5: o25ht += 1
    n_ht = len(ht_goals)
    avg_ft = sum(ft_goals) / nf if nf else 0
    avg_ht = sum(ht_goals) / n_ht if n_ht else 0
    variance = sum((x - avg_ft) ** 2 for x in ft_goals) / nf if nf > 0 else 0
    return {'n': nf, 'avg_for': sum(goals_for) / nf if nf else 0,
            'avg_against': sum(goals_against) / nf if nf else 0,
            'avg_ft': avg_ft, 'avg_ht': avg_ht,
            'over25_pct': over25 / nf if nf else 0, 'btts_pct': btts / nf if nf else 0,
            'form': form, 'std_dev': math.sqrt(variance), 'ft_goals': ft_goals,
            'points': points, 'ppj': points / nf if nf else 0}


def analyze_player_deep_profile(ldf, player_name):
    if ldf is None or ldf.empty: return None
    tl = player_name.strip().lower()
    mask = (ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)
    games = ldf[mask].copy()
    if games.empty: return None
    if 'datetime_obj' in games.columns and not games['datetime_obj'].isna().all():
        games = games.sort_values('datetime_obj', ascending=False)
    w5 = _compute_window_stats(games.head(5), tl)
    w15 = _compute_window_stats(games.head(15), tl)
    if not w5 or not w15: return None
    ppj_5 = w5['ppj']; ppj_15 = w15['ppj']; ppj_delta = ppj_5 - ppj_15
    if ppj_delta >= 0.5: trend, trend_icon = 'up', '📈'
    elif ppj_delta >= 0.2: trend, trend_icon = 'slight_up', '↗️'
    elif ppj_delta <= -0.5: trend, trend_icon = 'down', '📉'
    elif ppj_delta <= -0.2: trend, trend_icon = 'slight_down', '↘️'
    else: trend, trend_icon = 'stable', '➖'
    return {'w5': w5, 'w15': w15, 'trend': trend, 'trend_icon': trend_icon,
            'ppj_5': ppj_5, 'ppj_15': ppj_15, 'ppj_delta': ppj_delta,
            'form': w5['form']}


def compute_player_ranking_stats(ldf, player_name):
    if ldf is None or ldf.empty: return None
    tl = player_name.strip().lower()
    mask = (ldf['home_team'].str.lower() == tl) | (ldf['away_team'].str.lower() == tl)
    games = ldf[mask].copy()
    if games.empty: return None
    if 'datetime_obj' in games.columns and not games['datetime_obj'].isna().all():
        games = games.sort_values('datetime_obj', ascending=False)
    else: games = games.sort_values('time', ascending=False)
    games10 = games.head(10).reset_index(drop=True)
    games5 = games.head(5)
    n10 = len(games10); n5 = len(games5)
    if n10 == 0: return None
    wins = draws = losses = 0
    gp10 = gc10 = gp5 = gc5 = 0
    form = []
    over_ht = {'0.5': 0, '1.5': 0, '2.5': 0}
    over_ft = {'0.5': 0, '1.5': 0, '2.5': 0, '3.5': 0, '4.5': 0, '5.5': 0}
    btts_ht = btts_ft = ht_valid = player_over_15 = player_over_25 = 0
    for i, (_, g) in enumerate(games10.iterrows()):
        is_h = str(g['home_team']).strip().lower() == tl
        a = safe_int(g.get('home_score')); b = safe_int(g.get('away_score'))
        my = a if is_h else b; opp = b if is_h else a
        total_ft = a + b
        if i < n5: gp5 += my; gc5 += opp
        gp10 += my; gc10 += opp
        if my > opp: wins += 1; form.append('V')
        elif my < opp: losses += 1; form.append('D')
        else: draws += 1; form.append('E')
        for k, thr in [('0.5', 0.5), ('1.5', 1.5), ('2.5', 2.5), ('3.5', 3.5), ('4.5', 4.5), ('5.5', 5.5)]:
            if total_ft > thr: over_ft[k] += 1
        if a > 0 and b > 0: btts_ft += 1
        hth_r = g.get('ht_home'); hta_r = g.get('ht_away')
        hth = safe_int(hth_r) if hth_r is not None and not (isinstance(hth_r, float) and math.isnan(hth_r)) else None
        hta = safe_int(hta_r) if hta_r is not None and not (isinstance(hta_r, float) and math.isnan(hta_r)) else None
        if hth is not None and hta is not None:
            ht_total = hth + hta; ht_valid += 1
            for k, thr in [('0.5', 0.5), ('1.5', 1.5), ('2.5', 2.5)]:
                if ht_total > thr: over_ht[k] += 1
            if hth > 0 and hta > 0: btts_ht += 1
        if my >= 2: player_over_15 += 1
        if my >= 3: player_over_25 += 1
    points = wins * 3 + draws
    ppj = points / n10
    return {'player': player_name, 'J': n10, 'V': wins, 'E': draws, 'D': losses,
            'GP': gp10, 'GC': gc10, 'SG': gp10 - gc10, 'ppj': ppj, 'points': points,
            'form': form,
            'avg_gp_5': gp5 / n5 if n5 else 0, 'avg_gc_5': gc5 / n5 if n5 else 0,
            'avg_gp_10': gp10 / n10, 'avg_gc_10': gc10 / n10,
            'over_05_ht': over_ht['0.5'] / ht_valid if ht_valid else 0,
            'over_15_ht': over_ht['1.5'] / ht_valid if ht_valid else 0,
            'over_25_ht': over_ht['2.5'] / ht_valid if ht_valid else 0,
            'btts_ht': btts_ht / ht_valid if ht_valid else 0,
            'over_05_ft': over_ft['0.5'] / n10 if n10 else 0,
            'over_15_ft': over_ft['1.5'] / n10 if n10 else 0,
            'over_25_ft': over_ft['2.5'] / n10 if n10 else 0,
            'over_35_ft': over_ft['3.5'] / n10 if n10 else 0,
            'over_45_ft': over_ft['4.5'] / n10 if n10 else 0,
            'over_55_ft': over_ft['5.5'] / n10 if n10 else 0,
            'btts_ft': btts_ft / n10 if n10 else 0,
            'player_over_15': player_over_15 / n10 if n10 else 0,
            'player_over_25': player_over_25 / n10 if n10 else 0}


def generate_insights_players_pdf(ranking, liga):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.6 * cm, rightMargin=0.6 * cm,
                            topMargin=1 * cm, bottomMargin=1 * cm)
    els = []
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=16,
                             textColor=rl_colors.HexColor('#0099cc'),
                             alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold')
    sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=9,
                           textColor=rl_colors.HexColor('#666666'),
                           alignment=TA_CENTER, spaceAfter=10)
    foot_s = ParagraphStyle('F', parent=styles['Normal'], fontSize=7,
                            textColor=rl_colors.HexColor('#999999'), alignment=TA_CENTER)
    els.append(Paragraph("Insights Players — Ranking (Últimos 10 Jogos)", title_s))
    els.append(Paragraph(f"FIFAlgorithm | {liga} | {len(ranking)} players | "
                         f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_s))
    h1 = ['#', 'Jogador', 'J', 'V', 'E', 'D', 'PPJ', 'GP 5j', 'GP 10j', 'GC 5j', 'GC 10j']
    r1 = [[str(i), r['player'][:16], str(r['J']), str(r['V']), str(r['E']), str(r['D']),
           f"{r['ppj']:.2f}", f"{r['avg_gp_5']:.2f}", f"{r['avg_gp_10']:.2f}",
           f"{r['avg_gc_5']:.2f}", f"{r['avg_gc_10']:.2f}"] for i, r in enumerate(ranking, 1)]
    data = [h1] + r1
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#0099cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.3, rl_colors.grey)]))
    els.append(table)
    els.append(Spacer(1, 10))
    els.append(Paragraph("E-Soccer Fifa Analytics | @FIFAlgorithm", foot_s))
    doc.build(els)
    return buf.getvalue()


def generate_tips_pdf(df_f, ad, ld):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.5 * cm, rightMargin=0.5 * cm,
                            topMargin=0.8 * cm, bottomMargin=0.8 * cm)
    els = []
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=18,
                             textColor=rl_colors.HexColor('#00f5ff'),
                             alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold')
    sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=9,
                           textColor=rl_colors.HexColor('#7a89a8'),
                           alignment=TA_CENTER, spaceAfter=10)
    els.append(Paragraph("E-Soccer Fifa Analytics — Dicas do Dia", title_s))
    els.append(Paragraph(f"FIFAlgorithm | {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_f)} jogos", sub_s))

    header = ['Hora', 'Liga', 'Casa', 'Fora', 'HT', 'FT', 'Linha']
    data = [header]
    for _, r in df_f.iterrows():
        data.append([
            str(r.get('hora', '--:--')),
            str(r.get('competicao', ''))[:20],
            str(r.get('casa', ''))[:16],
            str(r.get('fora', ''))[:16],
            str(r.get('Gols HT', '-')),
            str(r.get('Gols FT', '-')),
            str(r.get('Linha Seg FT', '-')),
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#0099cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.3, rl_colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor('#f8f9fa')])]))
    els.append(table)
    doc.build(els)
    return buf.getvalue()


def generate_pdf(df, title="E-Soccer"):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=0.4 * cm, rightMargin=0.4 * cm,
                            topMargin=0.8 * cm, bottomMargin=0.6 * cm)
    els = []
    styles = getSampleStyleSheet()
    ts = ParagraphStyle('T', parent=styles['Title'], fontSize=14, spaceAfter=4)
    els.append(Paragraph(title, ts))
    els.append(Spacer(1, 6))
    header = [str(c) for c in df.columns]
    data = [header]
    for _, r in df.iterrows():
        data.append([str(v) if v is not None else '' for v in r.values])
    nc = len(df.columns)
    cw = [28.5 * cm / nc] * nc
    table = Table(data, colWidths=cw, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#0099cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.3, rl_colors.grey)]))
    els.append(table)
    doc.build(els)
    return buf.getvalue()


# ============================================
# RADAR
# ============================================
def compute_radar_from_fixtures(df_aceodds, ng=RADAR_GAMES):
    radar = {}
    if df_aceodds is None or df_aceodds.empty: return radar
    for liga in df_aceodds['competicao'].dropna().unique():
        df_liga = df_aceodds[df_aceodds['competicao'] == liga].copy()
        if df_liga.empty: continue
        if 'hora' in df_liga.columns:
            df_liga['_h'] = df_liga['hora'].apply(lambda x: safe_int(str(x).split(':')[0]) if x else 0)
            df_liga = df_liga.sort_values('_h')
        df_liga = df_liga.head(ng)
        n = len(df_liga)

        def avg_pct(col):
            if col not in df_liga.columns: return 0
            vals = []
            for v in df_liga[col]:
                s = str(v).strip()
                if s and s not in ('', '-', 'nan', 'None', 'NaN'):
                    try: vals.append(float(s.replace('%', '').strip()))
                    except: pass
            return (sum(vals) / len(vals) / 100) if vals else 0

        gh = pd.to_numeric(df_liga.get('Gols HT', pd.Series()), errors='coerce').mean()
        gf = pd.to_numeric(df_liga.get('Gols FT', pd.Series()), errors='coerce').mean()
        gh = 0 if pd.isna(gh) else gh; gf = 0 if pd.isna(gf) else gf
        if gf > 0: pct_ht = (gh / gf) * 100; pct_ft = 100 - pct_ht
        else: pct_ht = 50.0; pct_ft = 50.0
        if pct_ht >= 55:
            tendencia_tempo = '1º Tempo Forte'; badge_class = 'badge-ht-heavy'; tempo_icon = '🔥'
        elif pct_ft >= 55:
            tendencia_tempo = '2º Tempo Forte'; badge_class = 'badge-ft-heavy'; tempo_icon = '❄️'
        else:
            tendencia_tempo = 'Equilibrado'; badge_class = 'badge-balanced'; tempo_icon = '⚖️'
        o25f = avg_pct('Over 2.5 FT'); o35f = avg_pct('Over 3.5 FT'); o45f = avg_pct('Over 4.5 FT')
        o25h = avg_pct('Over 2.5 HT'); btf = avg_pct('BTTS FT')
        perfil = 'OFENSIVA' if gf >= 4.5 else ('EQUILIBRADA' if gf >= 3.2 else 'DEFENSIVA')
        score = round(min(gf / 6.0, 1) * 40 + o25f * 20 + o25h * 20 + btf * 20)
        radar[liga] = {'n': n, 'avg_ft': gf, 'avg_ht': gh,
                       'pct_ht': pct_ht, 'pct_ft': pct_ft,
                       'tendencia_tempo': tendencia_tempo,
                       'badge_class': badge_class, 'tempo_icon': tempo_icon,
                       'o25_ft': o25f, 'o35_ft': o35f, 'o45_ft': o45f,
                       'o25_ht': o25h, 'btts_ft': btf,
                       'perfil': perfil, 'score': score}
    return radar


def _build_reason_best(info, lg):
    reasons = []
    reasons.append(f"média de <b>{info['avg_ft']:.2f}</b> gols/jogo")
    if info['o25_ft'] >= 0.75: reasons.append(f"<span class='hl'>{info['o25_ft'] * 100:.0f}%</span> Over 2.5 FT")
    if info['o35_ft'] >= 0.55: reasons.append(f"<span class='hl'>{info['o35_ft'] * 100:.0f}%</span> Over 3.5 FT")
    if info['o25_ht'] >= 0.55: reasons.append(f"<span class='hl'>{info['o25_ht'] * 100:.0f}%</span> no 1º tempo")
    if info['btts_ft'] >= 0.7: reasons.append(f"BTTS em <span class='hl'>{info['btts_ft'] * 100:.0f}%</span>")
    return " · ".join(reasons)


# ============================================
# PAGE: JOGOS DO DIA
# ============================================
def page_jogos_do_dia():
    _render_html_safe(render_hero_v2())

    st.markdown('<div class="nav-v2">', unsafe_allow_html=True)
    nc1, nc2, nc3, nc4 = st.columns(4)

    with nc1:
        if st.button("💀 CARREGAR DADOS", key="load_leagues", width='stretch', type="primary"):
            with st.spinner("Carregando dados..."):
                try:
                    st.session_state['_fetch_errors'] = []
                    st.session_state['_profile_cache'] = {}
                    ad, dbg = {}, {}
                    prog = st.progress(0, text="Buscando ligas...")
                    for i, (ln, li) in enumerate(LEAGUES.items(), 1):
                        prog.progress(i / len(LEAGUES), text=f"Buscando {ln}...")
                        m = scraper.get_league_matches(li['id'])
                        if m:
                            rs = scraper.extract(m); dbg[ln] = scraper.last_debug
                            if rs:
                                d = pd.DataFrame(rs)
                                if 'datetime_obj' in d.columns and not d['datetime_obj'].isna().all():
                                    d = d.sort_values(by='datetime_obj', ascending=False)
                                else: d = d.sort_values(by='time', ascending=False)
                            else: d = pd.DataFrame()
                            ad[ln] = d
                        else:
                            ad[ln] = pd.DataFrame(); dbg[ln] = {'matched_today': 0}
                    prog.empty()
                    st.session_state['all_data'] = ad
                    st.session_state['debug_info'] = dbg
                    total_jogos = sum(len(x) for x in ad.values() if x is not None and not x.empty)
                    if total_jogos > 0: st.success(f"✅ {total_jogos} partidas carregadas")
                    else: st.info("Sem partidas finalizadas hoje ainda.")
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    with nc2:
        if st.button("⚡ ATUALIZAR JOGOS", key="load_games", width='stretch'):
            with st.spinner("Atualizando jogos..."):
                jogos = scrape_aceodds(max_retries=ACEODDS_MAX_RETRIES, timeout=ACEODDS_TIMEOUT)
                if jogos:
                    st.session_state['aceodds_games'] = jogos
                    st.session_state['aceodds_last_update'] = datetime.now()
                    st.session_state.ultima_oportunidade = set()
                    st.session_state['_profile_cache'] = {}
                    if not st.session_state.get('all_data'):
                        prog = st.progress(0, text="Carregando ligas...")
                        ad, dbg = {}, {}
                        for i, (ln, li) in enumerate(LEAGUES.items(), 1):
                            prog.progress(i / len(LEAGUES), text=f"Buscando {ln}...")
                            m = scraper.get_league_matches(li['id'])
                            if m:
                                rs = scraper.extract(m); dbg[ln] = scraper.last_debug
                                d = pd.DataFrame(rs) if rs else pd.DataFrame()
                                if not d.empty and 'datetime_obj' in d.columns:
                                    d = d.sort_values(by='datetime_obj', ascending=False)
                                ad[ln] = d
                            else:
                                ad[ln] = pd.DataFrame(); dbg[ln] = {'matched_today': 0}
                        prog.empty()
                        st.session_state['all_data'] = ad
                        st.session_state['debug_info'] = dbg
                    st.success(f"✅ {len(jogos)} jogos atualizados!"); st.rerun()
                else: st.error("❌ Não foi possível carregar.")

    with nc3:
        if st.button("📡 RADAR FIFA", key="go_radar", width='stretch'):
            st.session_state.page = 'radar'; st.rerun()

    with nc4:
        if st.button("🧠 INSIGHTS PLAYERS", key="go_insights", width='stretch'):
            st.session_state.page = 'insights_players'; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if 'aceodds_games' not in st.session_state or not st.session_state['aceodds_games']:
        st.markdown("""<div style="background: linear-gradient(90deg, rgba(255,214,0,0.15), rgba(255,140,0,0.08));
            padding: 16px 20px; border-radius: 10px; border-left: 4px solid #ffd600;
            color: #f0f5ff; font-size: 14px; margin: 15px 0;">
            <b style="color:#ffd600;">⚠️ Atenção</b> — Clique em <b>💀 CARREGAR DADOS</b> e depois em <b>⚡ ATUALIZAR JOGOS</b>.
        </div>""", unsafe_allow_html=True)
        return

    df = pd.DataFrame(st.session_state['aceodds_games'])
    df['competicao'] = df['competicao'].apply(normalize_league_name)
    ad = st.session_state.get('all_data', {})

    # Debug rápido
    errs = st.session_state.get('_fetch_errors', [])
    if errs:
        with st.expander(f"⚠️ Debug ({len(errs)} erros)", expanded=False):
            for e in errs: st.text(f"❌ {e}")

    if ad:
        jc, jf = compute_jc_jf(df, ad, LEAGUES)
        df['JC'], df['JF'] = jc, jf
        with st.spinner("Rodando Monte Carlo..."):
            r = monte_carlo_cached(df, ad)
        for c, v in r.items(): df[c] = v
        for c in ['Gols HT', 'Gols FT', 'xG Casa', 'xG Fora']:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        for c in EXTRA_COLUMNS:
            if c in df.columns and c not in ['Gols HT', 'Gols FT', 'xG Casa', 'xG Fora']:
                df[c] = df[c].fillna('').astype(str)
        st.session_state['aceodds_games'] = df.to_dict('records')
    else:
        df['JC'] = df['JF'] = 0
        for c in EXTRA_COLUMNS: df[c] = ''

    novas = check_oportunidades(df)
    if novas: emitir_alerta(novas)

    upd_time = st.session_state.get('aceodds_last_update', datetime.now()).strftime('%H:%M')
    hoje = datetime.now().strftime('%d/%m')
    st.markdown(render_info_row_v2(jogos=len(df), upd_time=upd_time, hoje=hoje), unsafe_allow_html=True)

    fc1, _sp = st.columns([3, 4])
    with fc1:
        liga_opts = ['🎮 Escolher Liga'] + [f"{info['icon']} {lg}" for lg, info in LEAGUES.items()]
        liga_sel = st.selectbox("Liga", liga_opts, key='sel_liga', label_visibility='collapsed')
        if liga_sel == '🎮 Escolher Liga': f_liga = '(todas)'
        else:
            f_liga = '(todas)'
            for lg in LEAGUES.keys():
                if lg in liga_sel: f_liga = lg; break

    df_f = df.copy()
    if f_liga != '(todas)':
        df_f = df_f[df_f['competicao'] == f_liga]

    if df_f.empty:
        st.info("Nenhum jogo atende aos filtros.")
        st.markdown(render_footer_v2(), unsafe_allow_html=True); return

    st.markdown('<div class="pill-actions">', unsafe_allow_html=True)
    pdf_c1, pdf_c2, _pdf_sp = st.columns([1.4, 1.4, 4])
    with pdf_c1:
        if st.button("📄 Gerar PDF de Dicas", key="gen_tips_pdf", width='stretch', type="primary"):
            with st.spinner(f"Gerando PDF..."):
                try:
                    st.session_state['tips_pdf_bytes'] = generate_tips_pdf(df_f, ad, LEAGUES)
                    st.session_state['tips_pdf_count'] = len(df_f)
                    st.success(f"✅ PDF gerado!")
                except Exception as e: st.error(f"Erro: {e}")
    with pdf_c2:
        if 'tips_pdf_bytes' in st.session_state:
            st.download_button(
                f"📥 Baixar PDF ({st.session_state.get('tips_pdf_count', 0)} jogos)",
                data=st.session_state['tips_pdf_bytes'],
                file_name=f"dicas_esoccer_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf", width='stretch', key='dl_tips_pdf')
    st.markdown('</div>', unsafe_allow_html=True)

    cache = st.session_state.get('_profile_cache', {})
    st.markdown(render_card_header(), unsafe_allow_html=True)

    for i, (_, row) in enumerate(df_f.iterrows()):
        casa_raw = str(row.get('casa', '')); fora_raw = str(row.get('fora', ''))
        lk = find_league_key(row.get('competicao', ''), LEAGUES)
        ldf = ad.get(lk) if lk and lk in ad else None
        pa = pb = None
        if ldf is not None:
            key_a = (lk, casa_raw.strip().lower()); key_b = (lk, fora_raw.strip().lower())
            if key_a not in cache: cache[key_a] = analyze_player_deep_profile(ldf, casa_raw)
            if key_b not in cache: cache[key_b] = analyze_player_deep_profile(ldf, fora_raw)
            pa, pb = cache[key_a], cache[key_b]
        st.markdown(render_card_row_v2(row, casa_raw, fora_raw, ldf=ldf, perfil_a=pa, perfil_b=pb), unsafe_allow_html=True)
        with st.expander(f"🔍 Análise completa — {casa_raw} × {fora_raw}", expanded=False):
            if ldf is not None:
                _render_html_safe(render_h2h_comparison(casa_raw, fora_raw, ldf,
                                                        hora=str(row.get('hora', '--:--')),
                                                        liga=str(row.get('competicao', ''))))
            render_match_card(row, ad, LEAGUES, idx=i)
    st.session_state['_profile_cache'] = cache

    st.markdown(render_footer_v2(), unsafe_allow_html=True)


# ============================================
# PAGE: RADAR
# ============================================
def render_radar_tab():
    _render_html_safe(render_hero_v2())

    st.markdown('<div class="nav-v2">', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("⬅️ VOLTAR AO MENU", key="radar_back", width='stretch', type="primary"):
            st.session_state.page = 'jogos_dia'; st.rerun()
    with b2:
        if st.button("📅 JOGOS DO DIA", key="radar_goto_jogos", width='stretch'):
            st.session_state.page = 'jogos_dia'; st.rerun()
    with b3:
        if st.button("🧠 INSIGHTS PLAYERS", key="radar_goto_ins", width='stretch'):
            st.session_state.page = 'insights_players'; st.rerun()
    with b4:
        st.markdown('<div style="padding:13px 16px;text-align:center;font-size:11.5px;font-weight:800;color:#00ff88;letter-spacing:0.8px;text-transform:uppercase;border:1.5px solid rgba(0,255,136,0.4);border-radius:10px;background:rgba(0,255,136,0.08);">🟢 Radar Ativo</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    df_ac = st.session_state.get('aceodds_games', None)
    if df_ac is None or (isinstance(df_ac, list) and not df_ac):
        st.warning("⚠️ Carregue os **Jogos do Dia** primeiro.")
        st.markdown(render_footer_v2(), unsafe_allow_html=True); return
    if isinstance(df_ac, list): df_ac = pd.DataFrame(df_ac)
    if df_ac.empty:
        st.info("Sem dados."); st.markdown(render_footer_v2(), unsafe_allow_html=True); return
    df_ac = df_ac.copy()
    df_ac['competicao'] = df_ac['competicao'].apply(normalize_league_name)
    radar = compute_radar_from_fixtures(df_ac, RADAR_GAMES)
    if not radar:
        st.warning("Sem dados."); st.markdown(render_footer_v2(), unsafe_allow_html=True); return
    rank = sorted(radar.items(), key=lambda x: -x[1]['score'])

    best_score = rank[0][1]['score'] if rank else 0
    total_ligas = len(radar)
    st.markdown(f"""<div class="info-v2-row">
        <div class="info-v2-card">
            <div class="info-v2-icon">📡</div>
            <div class="info-v2-content">
                <div class="info-v2-label">LIGAS ANALISADAS</div>
                <div class="info-v2-value">{total_ligas}</div>
            </div>
        </div>
        <div class="info-v2-card">
            <div class="info-v2-icon">🏆</div>
            <div class="info-v2-content" style="flex:1;">
                <div class="info-v2-label" style="color:#00f5ff;">MELHOR SCORE ENCONTRADO</div>
                <div class="info-v2-prob-text">{best_score} pts · {rank[0][0] if rank else '—'}</div>
            </div>
            <div class="info-v2-online"><span class="info-v2-dot"></span> ATIVO</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if rank:
        best_lg, best_info = rank[0]
        reason = _build_reason_best(best_info, best_lg)
        st.markdown(f"""<div class="league-card-best">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
                    <span class="best-badge">🏆 MELHOR PARA OVER GOLS</span>
                    <span style="font-size:22px; font-weight:900; color:#f0f5ff;">
                        {LEAGUES.get(best_lg, {}).get('icon', '⚽')} {best_lg}
                    </span>
                    <span class="{best_info['badge_class']}" style="font-size:12px; padding:6px 14px;">
                        {best_info['tempo_icon']} {best_info['tendencia_tempo']} ({best_info['pct_ht']:.0f}% HT)
                    </span>
                </div>
                <div style="font-size:32px; font-weight:900; color:#00ff88; font-family:'JetBrains Mono',monospace;">{best_info['score']}</div>
            </div>
            <div class="best-reason">
                <div style="font-size:11.5px; color:#7a89a8; text-transform:uppercase; font-weight:800; margin-bottom:4px;">💡 Por que está em destaque:</div>
                <div>{reason}</div>
            </div>
            <div class="thermometer" style="margin-top:14px;">
                <div style="width:{best_info['score']}%; background: linear-gradient(90deg, #00ff88, #00f5ff);"></div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-label">📊 Ranking Completo</div>', unsafe_allow_html=True)
    for i, (lg, info) in enumerate(rank[1:], 2):
        md = {2: '🥈', 3: '🥉'}.get(i, f'#{i}')
        bc = {'OFENSIVA': 'badge-ofensivo', 'EQUILIBRADA': 'badge-equilibrado',
              'DEFENSIVA': 'badge-defensivo'}[info['perfil']]
        st.markdown(f"""<div class="league-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                    <span style="font-size:16px; font-weight:800;">{md} {lg}</span>
                    <span style="font-size:11px; color:#7a89a8;">({info['n']} jogos)</span>
                    <span class="{bc}">{info['perfil']}</span>
                    <span class="{info['badge_class']}">{info['tempo_icon']} {info['tendencia_tempo']}</span>
                </div>
                <div style="font-size:24px; font-weight:900; color:#00f5ff;">{info['score']}</div>
            </div>
            <div class="thermometer"><div style="width:{info['score']}%;"></div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown(render_footer_v2(), unsafe_allow_html=True)


# ============================================
# PAGE: INSIGHTS PLAYERS
# ============================================
def render_insights_players_tab():
    _render_html_safe(render_hero_v2())

    st.markdown('<div class="nav-v2">', unsafe_allow_html=True)
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        if st.button("⬅️ VOLTAR AO MENU", key="insights_back", width='stretch', type="primary"):
            st.session_state.page = 'jogos_dia'; st.rerun()
    with n2:
        if st.button("📅 JOGOS DO DIA", key="ins_goto_jogos", width='stretch'):
            st.session_state.page = 'jogos_dia'; st.rerun()
    with n3:
        if st.button("📡 RADAR FIFA", key="ins_goto_radar", width='stretch'):
            st.session_state.page = 'radar'; st.rerun()
    with n4:
        st.markdown('<div style="padding:13px 16px;text-align:center;font-size:11.5px;font-weight:800;color:#00f5ff;letter-spacing:0.8px;text-transform:uppercase;border:1.5px solid rgba(0,245,255,0.4);border-radius:10px;background:rgba(0,245,255,0.08);">📊 Base: Últimos 10 Jogos</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    ad = st.session_state.get('all_data', {})
    df_ac = st.session_state.get('aceodds_games', None)

    if not ad:
        st.markdown("""<div style="background: linear-gradient(90deg, rgba(255,214,0,0.15), rgba(255,140,0,0.08));
            padding: 12px 18px; border-radius: 10px; border-left: 4px solid #ffd600; color: #f0f5ff;">
            <b style="color:#ffd600;">⚠️ Dados não carregados</b> — Volte para <b>📅 Jogos do Dia</b>.
        </div>""", unsafe_allow_html=True)
        st.markdown(render_footer_v2(), unsafe_allow_html=True); return

    st.markdown('<div class="section-label">🎯 Filtros</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 2])
    with c1:
        ligas_disp = sorted(ad.keys())
        liga_sel = st.selectbox("📌 Liga", ligas_disp, key='insights_liga_v5')
    with c2:
        apenas_hoje = st.toggle("🎮 Apenas players que jogam hoje", value=True, key='insights_so_hoje_v5')

    ldf = ad.get(liga_sel, pd.DataFrame())
    if ldf.empty:
        st.warning(f"Sem dados para **{liga_sel}**.")
        st.markdown(render_footer_v2(), unsafe_allow_html=True); return

    players_set = set()
    if apenas_hoje and df_ac is not None and not (isinstance(df_ac, list) and len(df_ac) == 0):
        if isinstance(df_ac, list): df_ac = pd.DataFrame(df_ac)
        df_ac = df_ac.copy()
        df_ac['competicao'] = df_ac['competicao'].apply(normalize_league_name)
        df_liga_hoje = df_ac[df_ac['competicao'] == liga_sel]
        for _, r in df_liga_hoje.iterrows():
            h = str(r.get('casa', '')).strip(); a = str(r.get('fora', '')).strip()
            if h: players_set.add(h)
            if a: players_set.add(a)
    if not players_set:
        for _, r in ldf.iterrows():
            h = str(r.get('home_team', '')).strip(); a = str(r.get('away_team', '')).strip()
            if h: players_set.add(h)
            if a: players_set.add(a)
    if not players_set:
        st.info("Sem players."); st.markdown(render_footer_v2(), unsafe_allow_html=True); return

    with st.spinner("Calculando ranking..."):
        ranking = []
        for p in players_set:
            s = compute_player_ranking_stats(ldf, p)
            if s and s['J'] > 0: ranking.append(s)
    if not ranking:
        st.info("Sem dados."); st.markdown(render_footer_v2(), unsafe_allow_html=True); return
    ranking.sort(key=lambda x: -x['ppj'])

    upd = datetime.now().strftime('%H:%M')
    st.markdown(f"""<div class="info-v2-row">
        <div class="info-v2-card">
            <div class="info-v2-icon">🎮</div>
            <div class="info-v2-content">
                <div class="info-v2-label">PLAYERS</div>
                <div class="info-v2-value">{len(ranking)}</div>
            </div>
        </div>
        <div class="info-v2-card">
            <div class="info-v2-icon">🕐</div>
            <div class="info-v2-content" style="flex:1;">
                <div class="info-v2-label" style="color:#00f5ff;">LIGA SELECIONADA</div>
                <div class="info-v2-prob-text">{liga_sel}</div>
            </div>
            <div class="info-v2-online"><span class="info-v2-dot"></span> {upd}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-label">🏆 Ranking de Performance</div>', unsafe_allow_html=True)

    def cor_gp(v):
        if v >= 2.5: return '#00ff88'
        if v >= 2.0: return '#00f5ff'
        if v >= 1.5: return '#ffd600'
        if v >= 1.0: return '#ff8c00'
        return '#ff2e88'

    def cor_gc(v):
        if v <= 1.0: return '#00ff88'
        if v <= 1.5: return '#00f5ff'
        if v <= 2.0: return '#ffd600'
        if v <= 2.5: return '#ff8c00'
        return '#ff2e88'

    def cor_pct(p):
        pct = p * 100
        if pct >= 80: return '#00ff88'
        if pct >= 60: return '#00f5ff'
        if pct >= 40: return '#ffd600'
        if pct >= 20: return '#ff8c00'
        return '#7a89a8'

    rows = ''
    for idx, r in enumerate(ranking, 1):
        ppj = r['ppj']
        ppj_c = '#00ff88' if ppj >= 2.5 else ('#00f5ff' if ppj >= 2.0 else ('#ffd600' if ppj >= 1.5 else '#ff8c00'))
        md = '🥇' if idx == 1 else ('🥈' if idx == 2 else ('🥉' if idx == 3 else f'#{idx}'))
        form_html = ''
        for f in r['form'][:10]:
            bg = '#00ff88' if f == 'V' else ('#ffd600' if f == 'E' else '#ff2e88')
            fc = '#05070f' if f in ('V', 'E') else '#ffffff'
            form_html += f'<span style="display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;border-radius:50%;background:{bg};color:{fc};font-size:9px;font-weight:900;margin:0 1.5px;">{f}</span>'
        rows += f'''<div class="rank-row r1">
            <div class="rank-pos">{md}</div>
            <div class="rank-name">{r['player'][:16]}</div>
            <div class="rank-num">{r['J']}</div>
            <div class="rank-form">{form_html}</div>
            <div class="rank-num" style="color:{ppj_c};font-weight:900;">{ppj:.2f}</div>
            <div class="rank-num" style="color:{cor_gp(r['avg_gp_5'])};">{r['avg_gp_5']:.2f}</div>
            <div class="rank-num" style="color:{cor_gp(r['avg_gp_10'])};">{r['avg_gp_10']:.2f}</div>
            <div class="rank-num" style="color:{cor_gc(r['avg_gc_5'])};">{r['avg_gc_5']:.2f}</div>
            <div class="rank-num" style="color:{cor_gc(r['avg_gc_10'])};">{r['avg_gc_10']:.2f}</div>
        </div>'''
    header = '''<div class="rank-header r1">
        <div class="rank-hcell">#</div><div class="rank-hcell">Jogador</div>
        <div class="rank-hcell">J</div><div class="rank-hcell">Forma</div>
        <div class="rank-hcell">PPJ</div><div class="rank-hcell">GP 5j</div>
        <div class="rank-hcell">GP 10j</div><div class="rank-hcell">GC 5j</div>
        <div class="rank-hcell">GC 10j</div></div>'''
    _render_html_safe(f'<div class="rank-list">{header}{rows}</div>')

    st.markdown('<div class="section-label">⏱️ Mercados HT</div>', unsafe_allow_html=True)
    rows2 = ''
    for idx, r in enumerate(ranking, 1):
        rows2 += f'''<div class="rank-row r2">
            <div class="rank-num" style="color:#7a89a8;">{idx}</div>
            <div class="rank-name">{r['player'][:16]}</div>
            <div class="rank-num">{r['J']}</div>
            <div class="rank-num" style="color:{cor_pct(r['over_05_ht'])};">{r['over_05_ht']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_15_ht'])};">{r['over_15_ht']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_25_ht'])};">{r['over_25_ht']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['btts_ht'])};">{r['btts_ht']*100:.0f}%</div>
        </div>'''
    header2 = '''<div class="rank-header r2">
        <div class="rank-hcell">#</div><div class="rank-hcell">Jogador</div>
        <div class="rank-hcell">J</div><div class="rank-hcell">O 0.5 HT</div>
        <div class="rank-hcell">O 1.5 HT</div><div class="rank-hcell">O 2.5 HT</div>
        <div class="rank-hcell">BTTS HT</div></div>'''
    _render_html_safe(f'<div class="rank-list">{header2}{rows2}</div>')

    st.markdown('<div class="section-label">⚽ Mercados FT</div>', unsafe_allow_html=True)
    rows3 = ''
    for idx, r in enumerate(ranking, 1):
        rows3 += f'''<div class="rank-row r3">
            <div class="rank-num" style="color:#7a89a8;">{idx}</div>
            <div class="rank-name">{r['player'][:16]}</div>
            <div class="rank-num">{r['J']}</div>
            <div class="rank-num" style="color:{cor_pct(r['over_05_ft'])};">{r['over_05_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_15_ft'])};">{r['over_15_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_25_ft'])};">{r['over_25_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_35_ft'])};">{r['over_35_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_45_ft'])};">{r['over_45_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['over_55_ft'])};">{r['over_55_ft']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['btts_ft'])};">{r['btts_ft']*100:.0f}%</div>
        </div>'''
    header3 = '''<div class="rank-header r3">
        <div class="rank-hcell">#</div><div class="rank-hcell">Jogador</div>
        <div class="rank-hcell">J</div><div class="rank-hcell">O 0.5</div>
        <div class="rank-hcell">O 1.5</div><div class="rank-hcell">O 2.5</div>
        <div class="rank-hcell">O 3.5</div><div class="rank-hcell">O 4.5</div>
        <div class="rank-hcell">O 5.5</div><div class="rank-hcell">BTTS</div></div>'''
    _render_html_safe(f'<div class="rank-list">{header3}{rows3}</div>')

    st.markdown('<div class="section-label">🎯 Gols Individuais</div>', unsafe_allow_html=True)
    rows4 = ''
    for idx, r in enumerate(ranking, 1):
        rows4 += f'''<div class="rank-row r4">
            <div class="rank-num" style="color:#7a89a8;">{idx}</div>
            <div class="rank-name">{r['player'][:16]}</div>
            <div class="rank-num">{r['J']}</div>
            <div class="rank-num" style="color:#00f5ff;">{r['avg_gp_10']:.2f}</div>
            <div class="rank-num" style="color:{cor_pct(r['player_over_15'])};">{r['player_over_15']*100:.0f}%</div>
            <div class="rank-num" style="color:{cor_pct(r['player_over_25'])};">{r['player_over_25']*100:.0f}%</div>
        </div>'''
    header4 = '''<div class="rank-header r4">
        <div class="rank-hcell">#</div><div class="rank-hcell">Jogador</div>
        <div class="rank-hcell">J</div><div class="rank-hcell">Méd GP</div>
        <div class="rank-hcell">+1.5</div><div class="rank-hcell">+2.5</div></div>'''
    _render_html_safe(f'<div class="rank-list">{header4}{rows4}</div>')

    st.markdown(render_footer_v2(), unsafe_allow_html=True)


# ============================================
# GLOBAL + SIDEBAR
# ============================================
scraper = EFootballScraper()
with st.sidebar:
    st.markdown("""<div class="sb-brand">
        <div class="sb-logo">🤖</div>
        <div>
            <div class="sb-brand-name">FIFAlgorithm</div>
            <div class="sb-brand-sub">E-Soccer Analytics</div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="sb-section">NAVEGAÇÃO</div>', unsafe_allow_html=True)
    for key, label in [('jogos_dia', '📅 Jogos do Dia'),
                       ('radar', '📡 Radar FIFA'),
                       ('insights_players', '🧠 Insights Players')]:
        active = st.session_state.page == key
        if st.button(label, key=f'nav_{key}', width='stretch',
                     type='primary' if active else 'secondary'):
            st.session_state.page = key; st.rerun()
    st.markdown('<div class="sb-section">LIGAS</div>', unsafe_allow_html=True)
    for lg_name, lg_info in LEAGUES.items():
        key = f'liga_{lg_name}'
        active = st.session_state.page == key
        if st.button(f"{lg_info['icon']} {lg_name}", key=f'nav_{key}', width='stretch',
                     type='primary' if active else 'secondary'):
            st.session_state.page = key; st.rerun()
    st.markdown("---")
    modo = st.toggle("☀️ Modo Claro", value=st.session_state.modo_claro, key='toggle_modo')
    if modo != st.session_state.modo_claro:
        st.session_state.modo_claro = modo; st.rerun()
    st.session_state.som_ativo = st.toggle("🔊 Som", value=st.session_state.som_ativo, key='toggle_som')
    st.session_state.notif_alerta = st.toggle("🔔 Notificações", value=st.session_state.notif_alerta, key='toggle_notif')
    if st.button("🔔 Testar Alerta", width='stretch'):
        play_alert_sound(); st.toast("🎯 Teste!", icon="🚨")
    if st.button("🌐 Testar Conexão 24live", width='stretch'):
        ok, msg = test_24live_connectivity()
        if ok: st.success(f"✅ {msg}")
        else: st.error(f"❌ {msg}")
    st.markdown(f"""<div class="sb-footer">
        FIFAlgorithm v6.13.0 - Streamlit
        <div class="sb-footer-user">
            <div class="sb-avatar">V</div>
            <div>
                <div style="font-size:12px; font-weight:700; color:#f0f5ff;">Vagner S</div>
                <div style="font-size:10px;">Conta ativa</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# ============================================
# ROUTER
# ============================================
page = st.session_state.get('page', 'jogos_dia')
if page == 'jogos_dia':
    page_jogos_do_dia()
elif page == 'insights_players':
    render_insights_players_tab()
elif page == 'radar':
    render_radar_tab()
else:
    page_jogos_do_dia()