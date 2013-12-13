# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'TradeTransaction.option_type'
        db.delete_column('trade_tradetransaction', 'option_type')

        # Adding field 'TradeTransaction.signal_type'
        db.add_column('trade_tradetransaction', 'signal_type',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=10, db_index=True),
                      keep_default=False)


        # Changing field 'TradeTransaction.type'
        db.alter_column('trade_tradetransaction', 'type', self.gf('django.db.models.fields.SmallIntegerField')())
        # Adding field 'SignalRequest.signal_type'
        db.add_column('trade_signalrequest', 'signal_type',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=10, db_index=True),
                      keep_default=False)


        # Changing field 'SignalRequest.state'
        db.alter_column('trade_signalrequest', 'state', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'SignalRequest.type'
        db.alter_column('trade_signalrequest', 'type', self.gf('django.db.models.fields.SmallIntegerField')())

    def backwards(self, orm):
        # Adding field 'TradeTransaction.option_type'
        db.add_column('trade_tradetransaction', 'option_type',
                      self.gf('django.db.models.fields.IntegerField')(default=1, db_index=True),
                      keep_default=False)

        # Deleting field 'TradeTransaction.signal_type'
        db.delete_column('trade_tradetransaction', 'signal_type')


        # Changing field 'TradeTransaction.type'
        db.alter_column('trade_tradetransaction', 'type', self.gf('django.db.models.fields.IntegerField')())
        # Deleting field 'SignalRequest.signal_type'
        db.delete_column('trade_signalrequest', 'signal_type')


        # Changing field 'SignalRequest.state'
        db.alter_column('trade_signalrequest', 'state', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'SignalRequest.type'
        db.alter_column('trade_signalrequest', 'type', self.gf('django.db.models.fields.IntegerField')())

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'market.broker': {
            'Meta': {'object_name': 'Broker'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'through': "orm['market.BrokerUserData']", 'symmetrical': 'False'})
        },
        'market.brokeruserdata': {
            'Meta': {'object_name': 'BrokerUserData'},
            'broker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Broker']"}),
            'customer_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_balance_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_balance': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'})
        },
        'market.signal': {
            'Meta': {'object_name': 'Signal'},
            'allowed_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['market.SignalType']", 'symmetrical': 'False'}),
            'brokers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['market.Broker']", 'symmetrical': 'False'}),
            'days_trial': ('django.db.models.fields.SmallIntegerField', [], {'default': '3'}),
            'desc_full': ('django.db.models.fields.TextField', [], {}),
            'desc_short': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_square': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_wide': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_signals'", 'to': "orm['auth.User']"}),
            'price': ('django.db.models.fields.SmallIntegerField', [], {}),
            'since': ('django.db.models.fields.DateField', [], {}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sites.Site']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'trade_num': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'win_ratio': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        'market.signaltype': {
            'Meta': {'object_name': 'SignalType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {'unique': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'trade.instrument': {
            'Meta': {'object_name': 'Instrument'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'asset_class': ('django.db.models.fields.IntegerField', [], {}),
            'broker': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['market.Broker']", 'through': "orm['trade.InstrumentBrokerData']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'symbol': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'trade.instrumentbrokerdata': {
            'Meta': {'unique_together': "(('broker', 'external_id'),)", 'object_name': 'InstrumentBrokerData'},
            'broker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Broker']"}),
            'data': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'external_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'broker_data'", 'to': "orm['trade.Instrument']"}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'trade.signalrequest': {
            'Meta': {'object_name': 'SignalRequest'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'data': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expire_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trade.Instrument']"}),
            'is_won': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '25', 'decimal_places': '5'}),
            'signal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Signal']"}),
            'signal_type': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'trade.tradetransaction': {
            'Meta': {'object_name': 'TradeTransaction'},
            'amount': ('django.db.models.fields.SmallIntegerField', [], {}),
            'broker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Broker']"}),
            'close_price': ('django.db.models.fields.DecimalField', [], {'db_index': 'True', 'null': 'True', 'max_digits': '25', 'decimal_places': '5', 'blank': 'True'}),
            'close_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'data': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'external_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trade.Instrument']"}),
            'is_demo': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_won': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'open_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '25', 'decimal_places': '5'}),
            'open_time': ('django.db.models.fields.DateTimeField', [], {}),
            'payout': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '25', 'decimal_places': '2'}),
            'pnl': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '25', 'decimal_places': '2'}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'signal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Signal']", 'null': 'True', 'blank': 'True'}),
            'signal_request': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trade.SignalRequest']", 'null': 'True', 'blank': 'True'}),
            'signal_type': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['trade']