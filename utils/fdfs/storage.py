from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client,get_tracker_conf
from django.conf import settings


class FDFSStorage(Storage):
    def __init__(self,client_conf = None,base_url=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url


    def _open(self,name,mode='rb'):
        pass

    def _save(self,name,content):
        client_conf_obj = get_tracker_conf(self.client_conf)
        client = Fdfs_client(client_conf_obj)
        # client = Fdfs_client({'host_tuple': ['192.168.0.106'],
        #                       'port': 22122,
        #                       'timeout': 30,
        #                       'name': 'Tracker Pool'})
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs失败')

        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        return False

    def url(self, name):
        return self.base_url + name




