import logging
import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from datetime import datetime, timedelta, date
from .settings import settings

logger = logging.getLogger(__name__)

class PlaidClient:
    def __init__(self):
        configuration = plaid.Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': settings.plaid_client_id,
                'secret': settings.plaid_secret,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def _get_plaid_host(self):
        env = (settings.plaid_env or "sandbox").lower()
        if env == "production":
            return plaid.Environment.Production
        if env in ("development", "dev"):
            return plaid.Environment.Development
        return plaid.Environment.Sandbox
    
    def create_link_token(self, user_id: str) -> dict:
        request_kwargs = {
            "products": [Products(p.strip()) for p in settings.plaid_products.split(",") if p.strip()],
            "client_name": settings.app_name,
            "country_codes": [CountryCode(c.strip()) for c in settings.plaid_country_codes.split(",") if c.strip()],
            "language": "en",
            "user": LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        }
        if settings.plaid_redirect_uri:
            request_kwargs["redirect_uri"] = settings.plaid_redirect_uri
        request = LinkTokenCreateRequest(**request_kwargs)
        
        response = self.client.link_token_create(request)
        return {
            "link_token": response['link_token'],
            "expiration": response['expiration']
        }
    
    def exchange_public_token(self, public_token: str) -> dict:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        
        return {
            "access_token": response['access_token'],
            "item_id": response['item_id']
        }
    
    def get_accounts(self, access_token: str) -> list:
        request = AccountsGetRequest(access_token=access_token)
        response = self.client.accounts_get(request)
        data = response.to_dict()
        return data.get('accounts', [])
    
    def get_transactions(self, access_token: str, start_date: datetime, end_date: datetime, count: int = 500) -> dict:
        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date
        page_size = min(count, 500)
        collected: list = []
        latest_accounts = []
        total = 0
        offset = 0
        request_count = 0

        while True:
            request_count += 1
            options = TransactionsGetRequestOptions(count=page_size, offset=offset)
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start,
                end_date=end,
                options=options
            )
            response = self.client.transactions_get(request).to_dict()
            latest_accounts = response.get('accounts', latest_accounts)
            batch = response.get('transactions', [])
            collected.extend(batch)
            total = response.get('total_transactions', len(collected))
            if len(collected) >= total:
                break
            offset = len(collected)
        logger.info(
            "Plaid transactions_get fetched %s transactions across %s request(s)",
            total,
            request_count,
        )
        return {
            "transactions": collected,
            "total_transactions": total,
            "accounts": latest_accounts,
            "request_count": request_count,
        }

_client = PlaidClient()

def create_link_token(user_id: str) -> dict:
    return _client.create_link_token(user_id)

def exchange_public_token(public_token: str) -> dict:
    return _client.exchange_public_token(public_token)

def get_accounts(access_token: str) -> list:
    return _client.get_accounts(access_token)

def get_transactions(access_token: str, start_date: datetime, end_date: datetime, count: int = 500) -> dict:
    return _client.get_transactions(access_token, start_date, end_date, count)
