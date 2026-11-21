#!/bin/sh
exec python -m streamlit run web_app.py --server.address 0.0.0.0 --server.port 8000
