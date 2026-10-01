from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from t_tech.invest import Client, AsyncClient
from t_tech.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from t_tech.invest.sandbox.client import SandboxClient

from core.config import settings


class InvestClient:
    """
    Единый клиент T-Invest API для всей мультиагентной системы.
    
    Автоматически переключается между sandbox и production
    в зависимости от settings.MODE.
    """

    def __init__(self) -> None:
        self.token = settings.INVEST_TOKEN
        self.account_id = settings.ACCOUNT_ID
        self.is_sandbox = settings.is_sandbox()

        # Выбираем правильный target
        self.target = (
            INVEST_GRPC_API_SANDBOX if self.is_sandbox else INVEST_GRPC_API
        )

    @contextmanager
    def get_client(self) -> Generator[Client | SandboxClient, None, None]:
        """
        Синхронный контекстный менеджер.
        Рекомендуется использовать именно его почти везде.
        """
        if self.is_sandbox:
            with SandboxClient(self.token) as client:
                yield client
        else:
            with Client(self.token, target=self.target) as client:
                yield client

    async def get_async_client(self) -> AsyncClient:
        """
        Асинхронный клиент (для стримов и тяжёлых операций).
        Не забывай закрывать вручную или использовать async with.
        """
        return AsyncClient(self.token, target=self.target)

    def get_account_id(self) -> str:
        """Быстрый доступ к account_id из настроек."""
        return self.account_id

    def __repr__(self) -> str:
        mode = "SANDBOX" if self.is_sandbox else "PRODUCTION"
        return f"<InvestClient mode={mode} account={self.account_id[:8]}...>"


# Глобальный экземпляр — используем его во всём проекте
invest_client = InvestClient()


# Удобные шорткаты
def get_client():
    """Алиас для invest_client.get_client()"""
    return invest_client.get_client()


def get_account_id() -> str:
    return invest_client.get_account_id()