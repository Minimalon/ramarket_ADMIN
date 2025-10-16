from pydantic import BaseModel, Field

from core.oneC.pd_model import User


class SendCash(BaseModel):
    shop_id: str = ''
    currency: str = ''
    amount: float = 0
    user: User | None = None

    def send_to_1c(self):
        return {
            "Shop": self.shop_id,
            "Amount": self.amount,
            "Currency": self.currency,
            "User": self.user.id
        }

class CreateOstatok(BaseModel):
    shop_id: str = ''
    currency: str = ''
    amount: str = 0
    user: User | None = None

    def send_to_1c(self):
        return {
            "Shop": self.shop_id,
            "Amount": self.amount,
            "Currency": self.currency,
            "User": self.user.id
        }
