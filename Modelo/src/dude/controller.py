import requests
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

class DudeConnectionBase:
    
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("DUDE_API")
        self.username = os.getenv("DUDE_USER")
        self.password = os.getenv("DUDE_PASSWORD")
        self.culture = "pt-BR"
        self.token_expiry = 120

    def get_current_date(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT00:00:00")

    def date_formatted(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S")

    def _get_token(self, endpoint: str) -> str:
        login_data = {
            'loginName': self.username,
            'Password': self.password,
            'cultureCode': self.culture,
            'Expires': self.token_expiry
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.post(
            f"{self.url}/{endpoint}",
            data=urlencode(login_data),
            headers=headers
        )
        resp.raise_for_status()

        return resp.text

    def _search_info(self, token: str, city: str, start_date: str, end_date: str):
        search_url = f"{self.url}/workorders/searches"
        all_orders = []
        page = 1
        total_pages = 1

        if(start_date == "vazio"):
            date = datetime.fromisoformat(self.get_current_date())
            start_date = date - relativedelta(months=1)
            start_date = start_date.isoformat()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Basic {token}"
        }

        while page <= total_pages:
            payload = {
                "Options": {
                    "PopulateCustomFields": True,
                    "PopulateMedium": True,
                    "PopulateSource": True,
                    "PopulateParentPaths": True,
                    "ParentPathDelimiter": "--",
                    "TotalItems": 0,
                    "TotalObjectCountOption": "TotalObjectCount"
                },
                "Page": {
                    "PageNumber": page,
                    "PageSize": 200
                },
                "City": {
                    "Filters": [{
                        "Value": city,
                        "MatchType": "Equals"
                    }]
                },
                "DateCreated": {
                    "StartValue": start_date,
                    "EndValue": end_date
                },
            }
            """ "DateLastModified": {
                "StartValue": "start_date_modified",
                "EndValue": "end_date_modified"
            } """

            resp = requests.post(search_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            all_orders.extend(data.get('Items', []))
            total_pages = data.get('TotalPages', 1)
            page += 1

        return all_orders

    def _filter(self, orders: list, status_filter: str) -> list:
        def should_include(o):
            if status_filter.lower() == "vazio":
                return True
            return (status_filter in (o.get("WOStatusName") or "")) \
                and bool(o.get("SourceAssetName"))

        mapped = []
        for o in orders:
            if should_include(o):
                mapped.append({
                    "IdOrdem":      o.get("WorkOrderNo", "Sem apontamento."),
                    "Nome":         o.get("Name", "Sem apontamento."),
                    "Problema":     o.get("ProblemName", "Sem apontamento."),
                    "Categoria":    o.get("WorkCategoryName", "Sem apontamento."),
                    "Setor":        o.get("SourceLocationName", "Sem apontamento."),
                    "Ativo":        o.get("SourceAssetName", "Sem apontamento."),
                    "Status":       o.get("WOStatusName", "Sem apontamento."),
                    "CriadoEm":     o.get("DateOriginated", "Sem apontamento."),
                    "TrabalhoReq":  o.get("WorkRequested", "Sem apontamento."),
                    "UltimaModif":  o.get("LastModifiedOn", "Sem apontamento."),
                    "DataEsperada": o.get("DateExpected", "Sem apontamento."),
                })
                
        if not mapped:
            return [{
                "IdOrdem":      "Sem informacao.",
                "Nome":         "Sem informacao.",
                "Problema":     "Sem informacao.",
                "Categoria":    "Sem informacao.",
                "Setor":        "Sem informacao.",
                "Ativo":        "Sem informacao.",
                "Status":       "Sem informacao.",
                "CriadoEm":     "Sem informacao.",
                "TrabalhoReq":  "Sem informacao.",
                "UltimaModif":  "Sem informacao.",
                "DataEsperada": "Sem apontamento",
            }]

        return mapped


    def fetch_new_requests(self, city, start_date, status_filter):
        token = self._get_token("login")
        end_date = self.date_formatted()

        orders = self._search_info(token, city, start_date, end_date)
        return self._filter(orders, status_filter)


if __name__ == "__main__":
    client = DudeConnectionBase()
    resultados = client.fetch_new_requests("Petropolis", "2025-05-10T06:00:00", "Completed")
    for ordem in resultados:
        s = (
            f"–– Ordem de Serviço ––\n"
            f"ID: {ordem['IdOrdem']}\n"
            f"Nome: {ordem['Nome']}\n"
            f"Problema: {ordem.get('Problema') or '—'}\n"
            f"Categoria: {ordem['Categoria']}\n"
            f"Setor: {ordem['Setor']}\n"
            f"Ativo: {ordem['Ativo']}\n"
            f"Status: {ordem['Status']}\n"
            f"Criado em: {ordem['CriadoEm']}\n"
            f"Trabalho requisitado: {ordem['TrabalhoReq'].strip()}\n"
            f"Última modificacao: {ordem['UltimaModif']}\n"
            f"Data Esperada: {ordem['DataEsperada']}\n"
        )
        print(s)
