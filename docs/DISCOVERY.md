# Discovery

The seed reference — Germany's Wahl-O-Mat (the Baden-Württemberg 2026 edition this project is
modeled on):

- https://www.wahl-o-mat.de/bw2026/app/main_app.html

## Research & data groundwork

The full research corpus now lives at the repo root and in [`../research/`](../research/).
**Start at the [README](../README.md)** for the document map, key design decisions, data-source
attribution, and the non-partisan disclaimer.
- https://github.com/Mcp-Brasil/mcp-brasil
    - TSE (documentação: https://github.com/augusto-herrmann/divulgacandcontas-doc):
        - Candidatos: https://github.com/Mcp-Brasil/mcp-brasil/blob/main/src/mcp_brasil/data/tse/client.py
        - Emendas parlamentares (aceita por autor): https://github.com/Mcp-Brasil/mcp-brasil/blob/main/src/mcp_brasil/data/transferegov/client.py
        - Diario oficial https://github.com/Mcp-Brasil/mcp-brasil/blob/main/src/mcp_brasil/data/diario_oficial/client.py
        - Bens declarados por candidatos: https://github.com/Mcp-Brasil/mcp-brasil/blob/main/src/mcp_brasil/datasets/tse_bens/tools.py
