from pathlib import Path
from collections import namedtuple

import httpx
from PySide6.QtCore import QObject, Signal, QRunnable, Slot


class ParserRunnerSignals(QObject):
    Parser_Connect_To_API_Failed_Signal = Signal(tuple)
    Parser_Completed_Signal = Signal(tuple)


class ParserRunner(QRunnable):
    """
    Get the version info:
    {version_id: nametuple(version_name, model_id, model_name, creator)}
    """
    def __init__(self, httpx_client: httpx.Client, version_id: str,
                 civitai_model_api_url: str = '',
                 civitai_version_api_url: str = ''):
        super().__init__()
        self.httpx_client = httpx_client
        self.version_id = version_id

        self.civitai_model_api_url = civitai_model_api_url or 'https://civitai.com/api/v1/models/'
        self.civitai_version_api_url = civitai_version_api_url or 'https://civitai.com/api/v1/model-versions/'

        self.signals = ParserRunnerSignals()
        self.version_info = namedtuple('version_info', 'version_name, model_id, model_name, creator')

    @Slot()
    def run(self) -> None:
        self.get_version_id_info()

    def get_version_id_info(self) -> None:
        try:
            r = self.httpx_client.get(self.civitai_version_api_url + self.version_id)
            version_data = r.json()
            version_name = version_data['name']
            model_id = str(version_data['modelId'])

            r = self.httpx_client.get(self.civitai_model_api_url + model_id)
            model_date = r.json()
            model_name = model_date['name']
            # assert model_name == version_data['model']['name']
            creator = model_date['creator']['username']

            version_id_info = {self.version_id: self.version_info(version_name, model_id, model_name, creator)}
            self.signals.Parser_Completed_Signal.emit((version_id_info, 'Preprocessing'))
        except Exception as e:
            self.signals.Parser_Connect_To_API_Failed_Signal.emit((f'versionId:{self.version_id}, {e}', 'Preprocessing'))


class DownloadRunnerSignals(QObject):
    download_failed_signal = Signal(tuple)
    download_completed_signal = Signal(tuple)


class DownloadRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, image_info: tuple, save_dir: Path,
                 categorize: bool, version_id_info_dict: dict | None,
                 civitai_image_api_url: str = ''):
        super().__init__()
        self.httpx_client = httpx_client
        # hint: image_info = (url_text, (modelVersionId, postId, imageId))
        self.image_original_url, self.image_params = image_info
        self.save_dir = save_dir
        self.categorize = categorize
        self.version_id_info_dict = version_id_info_dict
        self.model_name = ''
        self.version_name = ''

        self.civitai_image_api_url = civitai_image_api_url or 'https://civitai.com/api/v1/images'
        self.signals = DownloadRunnerSignals()

    @Slot()
    def run(self) -> None:
        self.save_dir = self.get_save_path()
        url = self.get_real_image_url() if self.image_params else self.image_original_url
        self.download_image(url)

    def get_save_path(self) -> Path:
        if not self.image_params or not self.categorize:
            return self.save_dir

        modelVersionId = self.image_params[0]
        if not modelVersionId:
            return self.save_dir / 'CIVIT_POST_Images'

        # Have to handle the model name like 'Skirt tug / dress tug / clothes tug'
        # hint: version_id_info_dict = {version_id1: nametuple(version_name, model_id, model_name, creator), ...}
        self.model_name = self.version_id_info_dict[modelVersionId].model_name.replace('/', '_').replace('\\', '_')
        self.version_name = self.version_id_info_dict[modelVersionId].version_name.replace('/', '_').replace('\\', '_')
        return self.save_dir / self.model_name / self.version_name / 'gallery'

    def get_real_image_url(self) -> str:
        modelVersionId, postId, imageId= self.image_params

        try:
            if not modelVersionId:
                params = {'postId': postId}
            elif postId:
                params = {'modelVersionId': modelVersionId,
                          'postId': postId}
            else:
                username = self.version_id_info_dict[modelVersionId].creator
                params = {'modelVersionId': modelVersionId,
                          'username': username}

            r = self.httpx_client.get(self.civitai_image_api_url, params=params)
            data = r.json()['items']
            if real_url := next((image['url'] for image in data if image['id'] == int(imageId)), ''):
                return real_url
        except Exception as e:
            print(e, f'raise Exception: get_real_image_url(), {r.url=}')
            return ''

    def download_image(self, url: str) -> None:
        if not url:
            self.signals.download_failed_signal.emit(
                (self.image_original_url,
                 self.model_name,
                 self.version_name,
                 'Fail to get a real url for API',
                 'Downloading',
                 self.image_params)
            )
            return

        self.save_dir.mkdir(parents=True, exist_ok=True)
        save_path = self.save_dir / Path(url.rsplit('/', 1)[-1])
        if save_path.exists():
            new_name = f'{save_path.stem}(repeat){save_path.suffix}'
            save_path = save_path.with_name(new_name)

        try:
            r = self.httpx_client.get(url)
            r.raise_for_status()

            with open(save_path, 'wb') as f:
                for date in r.iter_bytes():
                    if date:
                        f.write(date)

            self.signals.download_completed_signal.emit((f'{self.image_original_url}', 'Download success', 'Downloading'))
        except Exception as e:
            self.signals.download_failed_signal.emit(
                (self.image_original_url,
                 self.model_name,
                 self.version_name,
                 'Download failed',
                 'Downloading',
                 self.image_params)
            )
