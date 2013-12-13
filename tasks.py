import datetime
import logging

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

import celery
from decimal import *

from trade.brokers.goptions import GOptions
from market.models import Broker, BrokerUserData, Subscription
from trade.models import TradeTransaction, SignalRequest
from utils.decorators import single_instance_task
from accounts.conf import Event
from tc_accounts.tasks import notify_user
from django.db.models import F


logger = logging.getLogger('django')
logging.getLogger().setLevel(logging.INFO)


def _update_win_ratio(signal):
    try:
        # signal_trades = SignalRequest.objects.filter(signal=signal, state=SignalRequest.STATE_SUCCESS)
        dummy = User.objects.get(email=settings.DUMMY_USER)
        signal_trades = TradeTransaction.objects.filter(
            signal=signal,
            user=dummy,
            success=True
        ).exclude(close_price=None)
        signal.trade_num = len(signal_trades)

        # Ratio for last 30 days
        signal_trades_30d = signal_trades.filter(
            close_time__gt=(timezone.now() - datetime.timedelta(days=30))
        )
        signal.win_ratio = _calculate_win_ratio(signal_trades_30d)

        # Ratio for last 90 days
        signal_trades_90d = signal_trades.filter(
            close_time__gt=(timezone.now() - datetime.timedelta(days=90))
        )
        signal.win_ratio_long = _calculate_win_ratio(signal_trades_30d)

        # Total ratio
        signal.win_ratio_total = _calculate_win_ratio(signal_trades)

        signal.save()
    except Exception, e:
        logger.error('Update signal info', exc_info=True, extra={
            'signal': signal,
            'exception': e
        })


def _calculate_win_ratio(signal_trades_period):
    win_ratio = 0
    if len(signal_trades_period) >= 10:
        won_trades = len(signal_trades_period.filter(is_won=True))
        tie_trades = len(signal_trades_period.filter(close_price=F('open_price')))
        successful_trades = len(signal_trades_period) - tie_trades
        if successful_trades > 0:
            win_ratio = int(won_trades * 100 / successful_trades)
        if win_ratio < 50:
            win_ratio = 0
    return win_ratio


@celery.task
@single_instance_task(60 * 10)
def update_trades():
    counter = 0
    broker = Broker.objects.get(name='GOptions')
    g = GOptions()
    for position in TradeTransaction.objects.filter(close_price=None, success=True, close_time__lt=timezone.now()):
        customer_id = BrokerUserData.objects.get(broker=broker, user=position.user).customer_id
        data = g.get_customer_positions(customer_id, position.external_id)
        position.close_price = Decimal(data['endRate'])

        # If close price is still unknown, skip it
        if position.close_price == 0:
            continue

        position.close_time = timezone.make_aware(
            datetime.datetime.strptime(data['endDate'], "%Y-%m-%d %H:%M:%S"),
            timezone.utc)
        if position.open_price == 0:
            position.open_price = Decimal(data['entryRate'])
        position.data['final'] = data
        position.is_won = position.get_is_won()
        position.payout = Decimal(data['payout'])
        position.pnl = position.payout - position.amount
        position.is_demo = Decimal(data['isDemo'])
        position.save()

        signal_request = position.signal_request
        signal_request.is_won = position.is_won
        signal_request.save()

        counter += 1

        # Try to find a site ID
        # TODO: maybe put as part of TradeTransaction
        try:
            sub = Subscription.objects.filter(user=position.user, signal=position.signal, active=True)[0]
            site_id = sub.site.pk
        except:
            site_id = 1

        # Notify subscribers on position close event
        notify_user.delay(site_id, position.user, Event.POSITION_CLOSE, {
            'signal': position.signal,
            'trade_transaction': position,
            'currency': position.data.get('currency'),
        })

        # Notify signal owner on position close event
        # TODO: change email contents and enable
        # notify_user.delay(site_id, position.signal.owner, Event.POSITION_CLOSE_OWNER, {
        #     'signal': position.signal,
        #     'trade_transaction': position,
        #     'currency': position.data.get('currency'),
        # })

        # Update signal info
        _update_win_ratio(position.signal)

    logger.info('Updated GOptions transactions: %d' % counter)


@celery.task
def clear_cache():
    from django.core.cache import cache
    cache.clear()
