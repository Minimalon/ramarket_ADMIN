from datetime import datetime, timedelta

from core.oneC.api import Api
from core.utils.history_orders import create_excel_by_shops
from core.utils.send_email import send_email

api = Api()
async def send_email_historyOrders_today():
    response, all_shops = await api.get_all_shops()
    if not response.ok:
        return
    all_shops_id = [shop['id'] for shop in all_shops]
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.now() + timedelta(days=1)
    excel_path = await create_excel_by_shops(
        shops=all_shops_id,
        file_name=f'total_orders_today__{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
    )
    for to_email in ['ramil.akhmedov@rafinans.com', 'volkan.ileri@rafinans.com', 'abbas.gasanov@rafinans.com']:
        if excel_path is None:
            await send_email(
                subject=f'История продаж за {datetime.now().strftime("%Y-%m-%d")}',
                to_email=to_email,
                text='Отсутствуют продажи'
            )
        else:
            await send_email(
                subject=f'История продаж за {datetime.now().strftime("%Y-%m-%d")}',
                to_email=to_email,
                text='История продаж',
                file_path=excel_path
            )

if __name__ == '__main__':
    import asyncio
    asyncio.run(send_email_historyOrders_today())