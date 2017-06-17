# -*- coding: utf-8 -*-
'''
Created on 2017年4月20日

@author: chenyitao
'''

import os
import json
import gevent

from conf.default import HBaseSite
from common.models import Rule
from common.queues import CrawlerQueues
from common import TDDCLogging
from ..plugins import DBManager


class RulesUpdater(object):

    def __init__(self):
        '''
        Constructor
        '''
        TDDCLogging.info('-->Rules Updater Is Starting.')
        self._db = None
        self._idle = 0
        gevent.spawn(self._event)
        gevent.sleep()
        TDDCLogging.info('-->Rules Updater Was Started.')
        
    def _event(self):
        while True:
            if not CrawlerQueues.EVENT.empty():
                if not self._db:
                    self._wait = True
                    def _db_ready(params=None):
                        self._wait = False
                    self._db = DBManager('Rules Updater', HBaseSite.HBASE_NODES, _db_ready)
                    while self._wait:
                        gevent.sleep(0.2)
                event = CrawlerQueues.EVENT.get()
                if not event:
                    TDDCLogging.error('Update Rules Event Exception.')
                    continue
                self._update(event)
            else:
                if self._db and self._idle == 60:
                    self._db.hbase_instance().close()
                    self._db = None
                gevent.sleep(5)
                self._idle += 5

    def _get_local_conf(self, event):
        _conf_path = self.local_conf_path_base % event.platform
        if os.path.exists(_conf_path):
            with open(_conf_path, 'r') as f:
                return json.loads(f.read())
        return {}

    def _save_local_info(self, event, local_confs, remote_confs):
        new_confs = {}
        for remote_conf in remote_confs:
            key = remote_conf.get('package', None)
            if not key:
                continue
            new_confs[key] = remote_conf
        confs = json.dumps(new_confs)
        _conf_path = self.local_conf_path_base % event.platform
        if os.path.exists(_conf_path):
            os.remove(_conf_path)
        with open(_conf_path, 'a') as f:
            f.write(confs)

    def _get_update_list(self, event, local_confs):
        _update_list = []
        _remote_confs = None
        ret = self._db.hbase_instance().get(self.hbase_table,
                                            event.platform,
                                            self.hbase_family,
                                            self.hbase_index_qualifier)
        for column_value in ret.columnValues:
            _remote_confs = json.loads(column_value.value)
            for _remote_conf in _remote_confs:
                _package = _remote_conf['package']
            _remote_md5 = _remote_conf['md5']
            infos = local_confs.get(_package, None)
            _local_md5 = infos.get('md5') if infos else None
            if _local_md5 == _remote_md5:
                continue
            _update_list.append(_remote_conf)
        return _update_list, _remote_confs

    def _create_package(self, package):
        _paths = package.split('.')
        _path = './'
        for folder in _paths[:-1]:
            _path += folder + '/'
            if not os.path.exists(_path):
                os.mkdir(_path)
                with open(_path+'__init__.py', 'a') as _:
                    TDDCLogging.info('Make New Rules Package Success.')

    def _update_moulds(self, event, update_list):
        for item in update_list:
            _package = item['package']
            _md5 = item['md5']
            ret = self._db.hbase_instance().get(self.hbase_table,
                                                event.platform,
                                                self.hbase_family,
                                                _package.split('.')[-1])
            if not ret:
                TDDCLogging.error('Rules Fetch Exception.')
            self._create_package(_package)
            _file_path = './' + _package.replace('.', '/') + '.py'
            if os.path.exists(_file_path):
                os.remove(_file_path)
            with open(_file_path, 'a') as f:
                f.write(ret.columnValues[0].value)
            rule = Rule(event.platform, _package, item.get('moulds', None))
            CrawlerQueues.RULES_MOULDS_UPDATE.put(rule)

    def _update(self, event):
        _local_confs = self._get_local_conf(event) 
        _update_list, _remote_confs = self._get_update_list(event, _local_confs)
        if not len(_update_list):
            return
        self._update_moulds(event, _update_list)
        self._save_local_info(event, _local_confs, _remote_confs)

        
def main():
    pass

if __name__ == '__main__':
    main()