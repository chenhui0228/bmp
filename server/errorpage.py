import logging
logger = logging.getLogger('backup')

class page(object):
    content = None

    def __call__(self, status, message, traceback, version):
        logger.debug('status : %s , version : %s'%(status, version))
        logger.debug(traceback)
        if message:
            return message
        return self.content

    def set_content(self, content):
        self.content = content

class error_page_404(page):
    def __init__(self):
        self.content = '404 Error'

class error_page_405(page):
    def __init__(self):
        self.content = '405 Error'

class error_page_500(page):
    def __init__(self):
        self.content = '500 Error'

class error_page_403(page):
    def __init__(self):
        self.content = '403 Error'

class error_page_401(page):
    def __init__(self):
        self.content = '401 Error'

pages = {'error_page.404': error_page_404(),
         'error_page.405': error_page_405(),
         'error_page.500': error_page_500(),
         'error_page.403': error_page_403(),
         'error_page.401': error_page_401()
         }



if __name__ == '__main__':
    pass
