# -*- coding:utf-8 -*-
'''
Created on 2015年8月26日

@author: chenyitao
'''

import gevent

from common.queues import PLATFORM_PROXY_QUEUES
from worker.crawler.proxy_pool import CrawlProxyPool


class ProxyMiddleware(object):
    '''
    Proxy
    '''

    def process_request(self, request, spider):
        '''
        process request
        '''
        try:
            proxy = request.meta.get('proxy')
            if proxy:
                return
            task,_ = request.meta.get('item')
            ip_port = CrawlProxyPool.get_proxy(task.platform)
            ip, port = ip_port.split(':')
            proxy = '%s://%s:%s' % (task.proxy_type if task.proxy_type else 'http', ip, port)
            request.meta['proxy'] = proxy
            request.headers['X-Forwarded-For'] = '10.10.10.10'
            request.headers['X-Real-IP'] = '10.10.10.10'
        except Exception, e:
            print(e)


CURRENT_PROXY = None

class ProxyMiddlewareExtreme(object):
    '''
    Proxy
    '''

    def process_request(self, request, spider):
        '''
        process request
        '''
        global CURRENT_PROXY
        task = request.meta.get('item')
        if CURRENT_PROXY:
            self.set_proxy(task, request)
            return
        try:
            proxies = PLATFORM_PROXY_QUEUES.get(task.platform)
            while not proxies or not len(proxies):
                gevent.sleep(0.5)
                proxies = PLATFORM_PROXY_QUEUES.get(task.platform)
            ip_port = proxies.pop()
            CURRENT_PROXY = ip_port
            self.set_proxy(task, request)
        except Exception, e:
            print(e)

    def set_proxy(self, task, request):
        global CURRENT_PROXY
        proxy = '%s://%s' % (task.proxy_type, CURRENT_PROXY)
        request.meta['proxy'] = proxy
        request.headers['X-Forwarded-For'] = CURRENT_PROXY
        request.headers['X-Real-IP'] = CURRENT_PROXY
