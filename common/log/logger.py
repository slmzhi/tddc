# -*- coding: utf-8 -*-
'''
Created on 2017年5月9日

@author: chenyitao
'''

import logging
import sys

from common import singleton

@singleton
class TDDCLogger(object):
    
    def __init__(self):
        from conf.base_site import MODEL
        FORMAT = ('[%(levelname)s] [%(asctime)s] '
                  '[%(filename)s/:%(module)s:%(funcName)s:%(lineno)d] => %(message)s')
        logging.basicConfig(format=FORMAT, filename=MODEL.name+'.log') # @UndefinedVariable
        self._log = logging.getLogger(MODEL.name) # @UndefinedVariable
        self._init_logger()
    
    def _init_logger(self):
        self._log.setLevel(logging.DEBUG)
        stream = logging.StreamHandler()
        stream.setLevel(logging.DEBUG)
        fm_stream = logging.Formatter('\033[%(mytp)s;%(myfc)s;%(mybc)sm[%(levelname)s]'
                                      ' [%(asctime)s] %(mypath)s => %(message)s\033[0m')
        stream.setFormatter(fm_stream)
        self._log.addHandler(stream)
 
    @staticmethod
    def _update_kwargs(kwargs, tp, fc, bc, path=''):
        if not 'extra' in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['mytp'] = tp
        kwargs['extra']['myfc'] = fc
        kwargs['extra']['mybc'] = bc
        kwargs['extra']['mypath'] = path
    
    def get_cur_info(self):
        infos = sys._getframe()
        return (infos.f_back.f_back.f_code.co_filename,
#                 infos.f_back.f_back.f_code.co_name,
                infos.f_back.f_back.f_lineno)
        
    def debug(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs, '0', '31', '')
        self._log.debug(msg, *args, **kwargs)
 
    def info(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs, '0', '32', '')
        self._log.info(msg, *args, **kwargs)
 
    def warning(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs, '1', '37', '43')
        self._log.warning(msg, *args, **kwargs)
 
    def error(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs, '5', '37', '41', '[%s:%d]' % self.get_cur_info())
        self._log.error(msg, *args, **kwargs)
 
    def critical(self, msg, *args, **kwargs):
        self._update_kwargs(kwargs, '4', '37', '45', '[%(pathname)s/:%(lineno)d]')
        self._log.critical(msg, *args, **kwargs)


TDDCLogging = TDDCLogger()


def main():
    TDDCLogger().debug('msg')
    TDDCLogger().info('test')
    TDDCLogger().warning('test')
    TDDCLogger().error('msg')
    TDDCLogger().critical('msg')

if __name__ == '__main__':
    main()