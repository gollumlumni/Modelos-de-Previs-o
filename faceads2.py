from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
import pandas as pd
from os import system

system('cls')

ACCESS_TOKEN = 'EAAHDFQfaZAG8BO6DSJShHnKOZCBa2AGZAIsRFHobRN8hVEb0N2zY3UGiTD3Eu3l7IvdgtvPNZBFn3Bhpl8m6tZBu9UsVq7F1wpvUQPZA7GRo9GeyfUWA3I0Bu6VzZBsJOaRcJbQO8Yvh0j4Qdz8fNwKvKJuEVIuZChPAKMgSZBpUnCIWAnNTmHZCH7cJeyX1iKS8CN'

# id da conta do Madan
AD_ACCOUNT_ID = 'act_7621938624523227' 

# Inicializando
FacebookAdsApi.init(access_token=ACCESS_TOKEN)
ad_account = AdAccount(AD_ACCOUNT_ID)

# Parâmetros gerais da requisição
params = {
    'date_preset': 'this_year',
    'level': 'campaign'
}

# Buscar campanhas ativas para garantir que estamos pegando tudo corretamente
campaigns = ad_account.get_campaigns(fields=[
    'id',
    'name',
    'status',
    'objective',
    'start_time',
    'stop_time',
    'effective_status',
    'created_time',
    'updated_time',
    'buying_type',
    'attribution_setting'
], params=params)

# Criar dicionários para mapear ID da campanha -> Nome e Status
campaign_info = {campaign['id']: {
    'Nome da campanha': campaign['name'],
    'Veiculação da campanha': "Concluído" if campaign['status'] != 'ACTIVE' else "Ativo",
    'Tipo de orçamento do conjunto de anúncios': campaign.get('buying_type', 'N/A'),
    'Configuração de atribuição': campaign.get('attribution_setting', 'N/A')
} for campaign in campaigns}

# Definir os campos que queremos extrair dos insights
fields = [
    AdsInsights.Field.date_start,
    AdsInsights.Field.date_stop,
    AdsInsights.Field.campaign_id,
    AdsInsights.Field.campaign_name,
    AdsInsights.Field.impressions,
    AdsInsights.Field.reach,
    AdsInsights.Field.spend,
    AdsInsights.Field.cost_per_action_type,
    AdsInsights.Field.actions
]

# Obter insights das campanhas
insights = ad_account.get_insights(fields=fields, params=params)

# Definir prioridade das métricas de resultados
prioridade_metricas = [ 'reach', 'onsite_conversion.messaging_conversation_started_7d', 'link_click']

# Processar os dados para formatar como no CSV original
data = []
for insight in insights:
    campaign_id = insight['campaign_id']
    campaign_data = campaign_info.get(campaign_id, {})

    # Processar ações e custo por resultado
    action_type = "N/A"
    action_value = 0
    cost_per_result = "N/A"

    actions = insight.get('actions', [])
    
    # Selecionar a métrica correta com base na prioridade
    for tipo in prioridade_metricas:
        for action in actions:
            if action['action_type'] == tipo:
                action_type = tipo
                action_value = int(action['value'])
                break
        if action_type != "N/A":
            break

    cost_per_action = insight.get('cost_per_action_type', [])
    for cost in cost_per_action:
        if cost['action_type'] == action_type:
            cost_per_result = float(cost['value'])

    # Criar a linha formatada
    row = {
        "Início dos relatórios": insight.get('date_start', 'N/A'),
        "Término dos relatórios": insight.get('date_stop', 'N/A'),
        "Nome da campanha": campaign_data.get('Nome da campanha', 'N/A'),
        "Veiculação da campanha": campaign_data.get('Veiculação da campanha', 'N/A'),
        "Orçamento do conjunto de anúncios": "Usando o orçamento do conjunto de anúncios",
        "Tipo de orçamento do conjunto de anúncios": campaign_data.get('Tipo de orçamento do conjunto de anúncios', 'N/A'),
        "Configuração de atribuição": campaign_data.get('Configuração de atribuição', 'N/A'),
        "Resultados": action_value,
        "Indicador de resultados": action_type.replace("_", " ").capitalize(),  # Formata a métrica
        "Alcance": insight.get('reach', 0),
        "Impressões": insight.get('impressions', 0),
        "Custo por resultados": cost_per_result if cost_per_result != "N/A" else float(insight.get('spend', 0)) / max(1, action_value),
        "Valor usado (BRL)": float(insight.get('spend', 0)),
        "Término": insight.get('date_stop', 'N/A')
    }

    data.append(row)

# Criar DataFrame e exportar para XLSX
df = pd.DataFrame(data)
df.to_excel("facebook_ads_export.xlsx", index=False)
print("Arquivo salvo como 'facebook_ads_export.xlsx'")