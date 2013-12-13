import logging
import urllib
import urllib2
from xml.dom import minidom
import time
import datetime
import json
import re

from django.conf import settings
from django.core.cache import cache

from trade.models import Instrument, Broker, InstrumentBrokerData

logger = logging.getLogger(__name__)


class GOptionException(Exception):
    pass


class NoResults(GOptionException):
    pass


class WrongCredentials(GOptionException):
    pass


class GOptions(object):
    API_URL = 'http://www.api.goptions.com/Api'
    PLATFOM_DATA_URL = 'http://www.goptions.com/PlatformAjax/getJsonFile/PlatformData.json'

    def _textValue(self, node):
        return node[0].childNodes[0].nodeValue

    def _dictValue(self, node):
        ret = {}
        for n in node.childNodes:
            if n.childNodes:
                ret[n.nodeName] = n.childNodes[0].nodeValue
            else:
                ret[n.nodeName] = None
        return ret

    def with_proxy(fn):
        def wrapped(self, *args, **kwargs):
            if hasattr(settings, 'PROXY_ADDRESS'):
                passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passmgr.add_password(None, settings.PROXY_ADDRESS, settings.PROXY_USERNAME, settings.PROXY_PASSWORD)
                authinfo = urllib2.ProxyBasicAuthHandler(passmgr)
                proxy_support = urllib2.ProxyHandler({"http": settings.PROXY_ADDRESS})
                opener = urllib2.build_opener(proxy_support, authinfo)
                urllib2.install_opener(opener)
            return fn(self, *args, **kwargs)
        return wrapped

    def cache_by_ttl(fn):
        def cwrapped(self, *args, **kwargs):
            # check if ttl is actual
            key = fn.__name__
            platformData = cache.get(key)
            if(platformData is None):
                results = fn(self, *args, **kwargs)
                ttl = results[0]
                platformData = results[1]
                stl = (datetime.datetime.fromtimestamp(int(ttl)) - datetime.datetime.now()).seconds
                stl = min(180, stl)
                # store to cache with ttl
                cache.set(key, platformData, stl)
            return platformData
        return cwrapped

    @with_proxy
    def urlGetContent(self, data):
        params = urllib.urlencode(data)
        response = urllib2.urlopen(self.API_URL, params)
        return response.read()

    @with_proxy
    @cache_by_ttl
    def urlGetPlatformData(self):
        response = urllib2.urlopen(self.PLATFOM_DATA_URL)

        platform_data = json.loads(response.read())
        ttl = platform_data['attributes']['ttl']
        return ttl, platform_data

    def getOptionsAndAssets(self):
        platform_data = self.urlGetPlatformData()
        binaryOptions = platform_data['data']['binaryOptions']
        assets = platform_data['data']['assets']
        return binaryOptions, assets

    def filter_tradeble_rules(fn):
        def wrapped(self, *args, **kwargs):
            rules = fn(self, *args, **kwargs)
            # return [item for item in iterable if lambda item:]
            now = datetime.datetime.utcnow()
            daynum = now.isoweekday()

            def ffunc(rule):
                st = datetime.datetime.strptime(rule['startTime'], "%Y-%m-%d %H:%M:%S")
                et = datetime.datetime.strptime(rule['endTime'], "%Y-%m-%d %H:%M:%S")
                day_list = rule['weekDays'].split(",")
                if not(str(daynum) in day_list):
                    return False
                if st > now:
                    return False
                if et < now:
                    return False
                return True
            return filter(ffunc, rules)
        return wrapped

    #@filter_tradeble_rules
    def get_sixty_seconds_rules(self):
        platform_data = self.urlGetPlatformData()
        rules = platform_data['data']['rulesSixtySeconds']
        for rule in rules:
            asset = InstrumentBrokerData.objects.get(external_id=rule['assetId']).instrument
            rule['internal_id'] = asset.id
            rule['asset_name'] = asset.name
        return rules

    def get_options_builder_rules(self):
        rules = {}
        try:
            doc, raw_result = self.callAPI({
                'MODULE': 'Rules',
                'COMMAND': 'view',
                'FILTER[product]': 'optionsBuilder',
                'filter[rules]': 'live',

            })
            nodes = [self._dictValue(node) for node in doc.getElementsByTagName('Rules')[0].childNodes]
            assets = set([node['assetId'] for node in nodes])

            # group options rules by instrument
            for assetId in assets:
                try:
                    instrument = InstrumentBrokerData.objects.get(external_id=int(assetId)).instrument
                    rules[assetId] = {
                        'instrument': instrument,
                        'external_id': assetId,
                        'rules': []
                    }
                except InstrumentBrokerData.DoesNotExist:
                    pass
            for rule in nodes:
                rules[rule['assetId']]['rules'].append(rule)

        except Exception, e:
            logger.error('GOptions callAPI', exc_info=True, extra={
                'raw_result': raw_result,
                'exception': e
            })
        return rules

    def callAPI(self, data, batch_mode=False, skip_log=False):
        data['api_username'] = settings.GOPTIONS_API_USERNAME
        data['api_password'] = settings.GOPTIONS_API_PASSWORD
        data['api_whiteLabel'] = 'goptions'

        start_date = datetime.datetime.now()
        start_time = time.clock()

        raw_result = ''
        try:
            raw_result = self.urlGetContent(data)
            raw_result = re.sub(r"(?im)(?<=>)[\s]*", "", raw_result)
            xmldoc = minidom.parseString(raw_result)
        except Exception, e:
            logger.error('GOptions callAPI', exc_info=True, extra={
                'send_data': data,
                'raw_result': raw_result,
                'exception': e
            })
            raise e
        finally:
            if not skip_log:
                from market.tasks import scriber_log
                scriber_log.delay(
                    'goptions', 'call-api',
                    data={
                        'module': data.get('MODULE', 'BATCH'),
                        'command': data.get('COMMAND', '')},
                    extra={
                        'data': data,
                        'response': raw_result,
                    },
                    time=start_date,
                    latency=int((time.clock() - start_time) * 1000)
                )

        if len(xmldoc.getElementsByTagName('error')) > 0 and not batch_mode:
            error_msg = self._textValue(xmldoc.getElementsByTagName('error'))
            if error_msg == u'noResults':
                raise NoResults()
            else:
                logger.error('GOptions callAPI', exc_info=True, extra={
                    'send_data': data,
                    'raw_result': raw_result,
                    'error_message': error_msg
                })
                raise GOptionException(error_msg)
        if self._textValue(xmldoc.getElementsByTagName('connection_status')) != u'successful':
            logger.error('GOptions callAPI wrong credentials', exc_info=True, extra={
                'send_data': data,
                'raw_result': raw_result
            })
            raise WrongCredentials()
        return xmldoc, raw_result

    def get_customer_by_email(self, email):
        try:
            doc, raw_result = self.callAPI({
                'MODULE': 'Customer',
                'COMMAND': 'view',
                'FILTER[email]': email,
            })
            return self._dictValue(doc.getElementsByTagName('Customer')[0].childNodes[0])
        except:
            return None

    def get_customer_by_id(self, id):
        try:
            doc, raw_result = self.callAPI({
                'MODULE': 'Customer',
                'COMMAND': 'view',
                'FILTER[id]': id,
            })
            return self._dictValue(doc.getElementsByTagName('Customer')[0].childNodes[0])
        except:
            return None

    def update_instruments(self):
        broker = Broker.objects.get(name='GOptions')

        doc, raw_result = self.callAPI({
            'MODULE': 'Assets',
            'COMMAND': 'view',
            'FILTER[isTradeable]': 1,
        })

        instruments_list = doc.getElementsByTagName('Assets')[0].childNodes
        instruments_count = len(instruments_list)

        for asset in instruments_list:
            data = self._dictValue(asset)
            if data['type'] == 'commodities':
                asset_class = Instrument.ASSET_CLASS_COMMODITY
            elif data['type'] == 'currencies':
                asset_class = Instrument.ASSET_CLASS_CURRENCY
            elif data['type'] == 'indices':
                asset_class = Instrument.ASSET_CLASS_EQUITYINDEX
            elif data['type'] == 'stocks':
                asset_class = Instrument.ASSET_CLASS_STOCK
            instrument, created = Instrument.objects.get_or_create(symbol=data['symbol'], defaults={
                'name': data['name'],
                'asset_class': asset_class
            })

            ibdata, created = InstrumentBrokerData.objects.get_or_create(instrument=instrument, broker=broker, defaults={
                'external_id': data['id']
            })
            ibdata.data = data
            ibdata.external_id = data['id']
            ibdata.save()
        return instruments_count

    def get_open_options_by_instrument(self, assetId):
        try:
            doc, raw_result = self.callAPI({
                'MODULE': 'Options',
                'COMMAND': 'view',
                'FILTER[assetId]': assetId,
                'FILTER[status]': 'open'
            })
        except NoResults:
            return [], []

        option_list = []

        for option in doc.getElementsByTagName('Options')[0].childNodes:
            data = self._dictValue(option)
            if data['isActive'] != '1':
                continue
            option_list.append(data)

        return option_list

    def get_available_options(self, asset_id=None):
        options, assets = self.getOptionsAndAssets()
        # filter assets
        # get list of assets ids that have active option
        assetIds = set(map(lambda opt: opt['assetId'], options))

        if(asset_id):
            return [asset_id], filter(lambda opt: int(opt['assetId']) == int(asset_id), options)
        return assetIds, options

    def get_available_options_OLD(self, asset_id=None):
        try:
            doc, raw_result = self.callAPI({
                'MODULE': 'Options',
                'COMMAND': 'view',
            })
        except NoResults:
            return [], []

        instrument_ids = set()
        option_list = []

        for asset in doc.getElementsByTagName('Options')[0].childNodes:
            for option in asset.childNodes:
                data = self._dictValue(option)

                if 'status' in data and data['status'] != 'open':
                    continue

                if asset_id and int(data['assetId']) != asset_id:
                    continue

                instrument_ids.add(data['assetId'])

                option_list.append(data)

        return instrument_ids, option_list

    def add_sixty_seconds_positions(self, customer_id, position, amount, asset_id, rule_id):
        return self.add_position_core({
            'MODULE': 'Positions',
            'COMMAND': 'add',
            'product': 'sixtySeconds',
            'customerId': customer_id,
            'position': position,  # call/put
            'amount': amount,
            'ruleId': rule_id,
            'assetId': asset_id,
        })

    def add_option_builder_positions(self, customer_id, position, amount, rule_id, expireTime, asset_id):
        """MODULE=Positions&COMMAND=add&product=optionsBuilder&customerId=2&position=call&amoun
t=100&ruleId=3&expireTime=1324548000"""
        return self.add_position_core({
                'MODULE': 'Positions',
                'COMMAND': 'add',
            'product': 'optionsBuilder',
                'customerId': customer_id,
                'position': position,  # call/put
                'amount': amount,
                'assetId': asset_id,
                'ruleId': rule_id,
            'expireTime': expireTime,
            })

    def add_position(self, customer_id, position, amount, option_id, asset_id, rule_id):
        return self.add_position_core({
            'MODULE': 'Positions',
            'COMMAND': 'add',
            'customerId': customer_id,
            'position': position,  # call/put
            'amount': amount,
            'optionId': option_id,
            'assetId': asset_id,
            'ruleId': rule_id,
        })

    def add_position_core(self, request_data):
        success = False
        data = {}
        try:
            doc, raw_result = self.callAPI(request_data)
            if self._textValue(doc.getElementsByTagName('operation_status')) == u'successful':
                success = True
                data = self._dictValue(doc.getElementsByTagName('Positions')[0])
            else:
                logger.error('GOptions add_position_core', exc_info=True, extra={
                    'locals': locals(),
                    'raw_result': raw_result
                })
        except Exception, e:
            logger.error('GOptions add_position_core', exc_info=True, extra={
                'locals': locals(),
                'exception': e
            })
        return success, data

    def add_multiple_positions(self, positions):
        results = []
        raw_result = ''
        try:
            batches = {}
            i = 0
            for pos in positions:
                batches.update({
                    'BATCH[%d][MODULE]' % i: 'Positions',
                    'BATCH[%d][COMMAND]' % i: 'add',
                    'BATCH[%d][customerId]' % i: pos['customer_id'],
                    'BATCH[%d][position]' % i: pos['position'],  # call/put
                    'BATCH[%d][amount]' % i: pos['amount'],
                    'BATCH[%d][assetId]' % i: pos['asset_id'],
                    'BATCH[%d][ruleId]' % i: pos['rule_id'],
                })
                if 'option_id' in pos:
                    batches.update({
                        'BATCH[%d][optionId]' % i: pos['option_id']
                    })
                if 'product' in pos:
                    batches.update({
                        'BATCH[%d][product]' % i: pos['product']
                    })
                i += 1

            doc, raw_result = self.callAPI(batches, batch_mode=True)

            i = 0
            for pos in positions:
                doc_batch = doc.getElementsByTagName('BATCH_%d' % i)[0]
                if self._textValue(doc_batch.getElementsByTagName('operation_status')) == u'successful':
                    success = True
                    data = self._dictValue(doc_batch.getElementsByTagName('Positions')[0])
                else:
                    # logger.error('GOptions add_position single', exc_info=True, extra={
                    #     'locals': locals(),
                    #     'raw_result': raw_result
                    # })
                    success = False
                    is_insufficient_funds = False
                    is_min_amount = False
                    is_option_closed = False

                    try:
                        error_text = self._textValue(doc_batch.getElementsByTagName('error'))
                    except:
                        try:
                            error_text = self._textValue(doc_batch.getElementsByTagName('errors'))
                        except:
                            error_text = ''
                    error_text = error_text or ''
                    if u'insufficientFunds' in error_text:
                        is_insufficient_funds = True
                    if error_text[:11] == u'minAmountIs':
                        is_min_amount = error_text[11:]
                    if error_text == u'optionIsClosed':
                        is_option_closed = True
                    data = {
                        'error': doc_batch.toxml(),
                        'is_insufficient_funds': is_insufficient_funds,
                        'is_min_amount': is_min_amount,
                        'is_option_closed': is_option_closed,
                    }
                results.append({
                    'position': pos,
                    'success': success,
                    'data': data
                })
                i += 1
        except Exception, e:
            logger.error('GOptions add_position', exc_info=True, extra={
                'locals': locals(),
                'exception': e
            })
        return results, raw_result

    def get_customer_positions(self, customer_id, position_id=None):
        if position_id:
            req_filters = [
                ('FILTER[id]', position_id)
            ]
        else:
            # combine all open positions and last week closed positions
            req_filters = [
                ('FILTER[status]', 'open'),
                ('FILTER[date][min]', (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y_%m_%d 00:00'))
            ]

        position_list = {}

        for req_add in req_filters:
            req = {
                'MODULE': 'Positions',
                'COMMAND': 'view',
                'FILTER[customerId]': customer_id,
                req_add[0]: req_add[1]
            }

            try:
                doc, raw_result = self.callAPI(req)
                for position in doc.getElementsByTagName('Positions')[0].childNodes:
                    p = self._dictValue(position)
                    p['is_open'] = (p['status'] == 'open')
                    p['is_won'] = (p['status'] == 'won')
                    p['is_call'] = (p['position'] == 'call')
                    p['is_60'] = (p['sixtySeconds'] == 1)
                    position_list[p['id']] = p
            except NoResults:
                pass

        position_list = position_list.values()
        if position_id and len(position_list) > 0:
            return position_list[0]
        return position_list

    def get_asset_history(self, asset_id):
        doc, raw_result = self.callAPI({
            'MODULE': 'AssetsHistory',
            'COMMAND': 'view',
            'FILTER[assetId]': asset_id
        })

        rate_list = []
        for rate in doc.getElementsByTagName('AssetsHistory')[0].childNodes:
            r = self._dictValue(rate)
            rate_list.append((
                int(time.mktime(datetime.datetime.strptime(r['date'], "%Y-%m-%d %H:%M:%S").timetuple())) * 1000,
                float(r['rate'])
            ))

        return rate_list

    def get_last_rate(self, asset_id):
        min_date = datetime.datetime.now() - datetime.timedelta(minutes=3)
        doc, raw_result = self.callAPI({
            'MODULE': 'AssetsHistory',
            'COMMAND': 'view',
            'FILTER[assetId]': asset_id,
            'FILTER[date][min]': min_date.strftime("%Y-%m-%d %H:%M:%S")
        }, skip_log=True)

        nodes = doc.getElementsByTagName('AssetsHistory')[0].childNodes
        rate = nodes[nodes.length - 1]
        r = self._dictValue(rate)
        return float(r['rate'])
