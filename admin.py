from django.contrib import admin
from django.utils.timezone import localtime

from .models import Instrument, SignalRequest, TradeTransaction, InstrumentBrokerData
from utils.admin_filters import SkipDummyListFilter

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'asset_class')
    list_filter = ('asset_class',)

admin.site.register(Instrument, InstrumentAdmin)


class SignalRequestAdmin(admin.ModelAdmin):
    list_display = ('signal', 'instrument', 'type', 'signal_type', 'state', 'l10n_date', 'l10n_expire_time', 'price', 'is_won')
    list_filter = ('signal', 'type', 'signal_type', 'state', 'is_won', 'instrument')

    def l10n_date(self, row):
        return localtime(row.date).strftime(TIME_FORMAT)

    def l10n_expire_time(self, row):
        return localtime(row.expire_time).strftime(TIME_FORMAT)

    l10n_date.admin_order_field = 'date'
    l10n_date.short_description = 'Execution time'
    l10n_expire_time.admin_order_field = 'expire_time'
    l10n_expire_time.short_description = 'Expire time'

admin.site.register(SignalRequest, SignalRequestAdmin)


class TradeTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'signal', 'instrument', 'type', 'signal_type', 'amount', 'payout', 'pnl',
                    'l10n_open_time', 'l10n_close_time', 'open_price', 'close_price', 'external_id',
                    'success', 'is_won', 'read_only', 'is_demo')
    list_filter = ('signal', 'user', 'broker', 'success', 'read_only', 'is_won',
                   'is_demo', 'instrument', 'type', 'signal_type', SkipDummyListFilter)

    def l10n_open_time(self, row):
        return localtime(row.open_time).strftime(TIME_FORMAT)

    def l10n_close_time(self, row):
        return localtime(row.close_time).strftime(TIME_FORMAT)

    l10n_open_time.admin_order_field = 'open_time'
    l10n_open_time.short_description = 'Open time'
    l10n_close_time.admin_order_field = 'close_time'
    l10n_close_time.short_description = 'Close time'

admin.site.register(TradeTransaction, TradeTransactionAdmin)


class InstrumentBrokerDataAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'broker', 'external_id', 'last_update')
    list_filter = ('broker', 'instrument')
    search_fields = ('instrument__symbol', 'instrument__name')

admin.site.register(InstrumentBrokerData, InstrumentBrokerDataAdmin)
