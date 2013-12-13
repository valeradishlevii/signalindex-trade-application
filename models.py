from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tc_instruments.models import BaseInstrument

from jsonfield import JSONField

from market.models import Signal, Broker, SignalType


class InstrumentSortedManager(models.Manager):
    def get_query_set(self):
        return super(InstrumentSortedManager, self).get_query_set().order_by('name')


class Instrument(BaseInstrument):
    broker = models.ManyToManyField(Broker, through='InstrumentBrokerData')

    objects = InstrumentSortedManager()


class InstrumentBrokerData(models.Model):
    instrument  = models.ForeignKey(Instrument, related_name='broker_data')
    broker      = models.ForeignKey(Broker)
    external_id = models.IntegerField()
    data        = JSONField()
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('broker', 'external_id')


class SignalRequest(models.Model):
    TYPE_CALL = 1
    TYPE_PUT  = 2
    TYPES = (
        (TYPE_CALL, _('call')),
        (TYPE_PUT,  _('put')),
    )

    STATE_PENDING = 1
    STATE_SUCCESS = 2
    STATE_FAILED  = 3
    STATES = (
        (STATE_PENDING, _('Pending')),
        (STATE_SUCCESS, _('Success')),
        (STATE_FAILED,  _('Failed')),
    )

    signal      = models.ForeignKey(Signal)
    signal_type = models.SmallIntegerField(choices=SignalType.TYPES, db_index=True)
    instrument  = models.ForeignKey(Instrument)
    type        = models.SmallIntegerField(_('Type'), choices=TYPES)
    state       = models.SmallIntegerField(_('State'), choices=STATES, default=STATE_PENDING)
    is_won      = models.BooleanField(default=False)
    expire_time = models.DateTimeField()
    price       = models.DecimalField(max_digits=25, decimal_places=5)
    double_trade_size = models.BooleanField(_('Double Trade Size'), default=False)
    comment     = models.TextField(null=True, blank=True)
    data        = JSONField()
    date        = models.DateTimeField(_('Execution time'), auto_now_add=True)

    def __unicode__(self):
        return "%s [%s] %s (%s)" % (self.instrument.name, self.get_type(), self.signal.name, self.date.strftime("%Y-%m-%d %H:%M:%S"))

    def get_type(self):
        return dict(self.TYPES)[self.type]

    def is_pending(self):
        return self.state == self.STATE_PENDING


class TradeTransaction(models.Model):
    user           = models.ForeignKey(User)
    signal_request = models.ForeignKey(SignalRequest, null=True, blank=True)
    signal         = models.ForeignKey(Signal, null=True, blank=True)
    signal_type    = models.SmallIntegerField(choices=SignalType.TYPES, db_index=True)
    instrument     = models.ForeignKey(Instrument)
    broker         = models.ForeignKey(Broker)
    read_only      = models.BooleanField(db_index=True)
    type           = models.SmallIntegerField(_('Type'), choices=SignalRequest.TYPES)
    amount         = models.SmallIntegerField()
    open_price     = models.DecimalField(max_digits=25, decimal_places=5)
    open_time      = models.DateTimeField()
    close_price    = models.DecimalField(max_digits=25, decimal_places=5, null=True, blank=True, db_index=True)
    close_time     = models.DateTimeField(null=True, blank=True)
    pnl            = models.DecimalField(max_digits=25, decimal_places=2, default=0)
    payout         = models.DecimalField(max_digits=25, decimal_places=2, default=0)
    is_demo        = models.BooleanField(db_index=True)
    success        = models.BooleanField(db_index=True)
    is_won         = models.BooleanField(default=False, db_index=True)
    external_id    = models.IntegerField(null=True, blank=True)
    double_trade_size = models.BooleanField(_('Double Trade Size'), default=False)
    data           = JSONField()

    def __unicode__(self):
        return "[%s] [%s] %s %d @ %f" % (self.user, self.signal, self.instrument.name, self.amount, self.open_price)

    @staticmethod
    def get_user_transactions(user):
        return TradeTransaction.objects.filter(user=user, success=True).values_list('external_id', flat=True)

    def get_position(self):
        return dict(SignalRequest.TYPES)[self.type]

    def get_is_won(self):
        final = self.data.get('final')
        if final:
            result = final.get('is_won')
            if result:
                return result
        if self.close_price:
            if self.type == SignalRequest.TYPE_CALL:
                return self.close_price > self.open_price
            else:
                return self.close_price < self.open_price
        return False

    # def get_payout(self):
    #     final = self.data.get('final')
    #     if final:
    #         return final.get('payout') or 0
    #     return 0

    def get_is_insufficient_funds(self):
        return self.data.get('is_insufficient_funds', False)

    def get_is_min_amount(self):
        return self.data.get('is_min_amount', False)

    def get_is_option_closed(self):
        return self.data.get('is_option_closed', False)
