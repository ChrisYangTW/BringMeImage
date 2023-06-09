from pathlib import Path

import httpx

from PySide6.QtCore import QObject, Signal, QRunnable, Slot


class ParserRunnerSignals(QObject):
    Parser_connect_to_api_failed_signal = Signal(str)
    Parser_completed_signal = Signal(tuple)


class ParserRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, model_id='', version_id=''):
        super().__init__()
        self.httpx_client = httpx_client
        self.model_id = model_id
        self.version_id = version_id

        self.signals = ParserRunnerSignals()
        self.civitai_model_api_url = 'https://civitai.com/api/v1/models/'
        self.civitai_version_api_url = 'https://civitai.com/api/v1/model-versions/'

    @Slot()
    def run(self) -> None:
        if self.model_id:
            self.get_model_name(self.model_id)
        else:
            self.get_version_name(self.version_id)

    def get_model_name(self, model_id: str) -> None:
        try:
            r = self.httpx_client.get(self.civitai_model_api_url+model_id)
            self.signals.Parser_completed_signal.emit((True, {model_id: r.json()["name"]}))
        except Exception as e:
            self.signals.Parser_connect_to_api_failed_signal.emit(f'model:{model_id}, {e}')

    def get_version_name(self, version_id: str) -> None:
        try:
            r = self.httpx_client.get(self.civitai_version_api_url+version_id)
            self.signals.Parser_completed_signal.emit((False, {version_id: r.json()["name"]}))
        except Exception as e:
            self.signals.Parser_connect_to_api_failed_signal.emit(f'version:{version_id}, {e}')


class DownloadRunnerSignals(QObject):
    download_started_signal = Signal(str)
    download_connect_to_api_failed_signal = Signal(str)
    download_completed_signal = Signal(str)

class DownloadRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, image_info: tuple, save_dir: Path, model_and_version_name: tuple):
        super().__init__()
        self.httpx_client = httpx_client
        # (model_id, model_version_id, post_id, image_id)
        self.image_original_url, self.image_params = image_info
        self.save_dir = save_dir

        self.signals = DownloadRunnerSignals()
        self.civitai_image_api_url = 'https://civitai.com/api/v1/images?'

        if model_and_version_name:
            self.model_name_dict, self.version_name_dict = model_and_version_name

    @Slot()
    def run(self) -> None:
        self.save_dir = self.get_save_path()
        url = self.get_real_image_url() if self.image_params else self.image_original_url
        self.download_image(url)

    def get_save_path(self) -> Path:
        if not self.image_params:
            return Path(self.save_dir)

        model_name = self.model_name_dict[self.image_params[0]]
        version_name = self.version_name_dict[self.image_params[1]]
        return Path(self.save_dir) / Path(model_name) / Path(version_name) / Path('gallery')


    def get_real_image_url(self) -> str:
        model_id, model_version_id, post_id, image_id = self.image_params
        try:
            url = f'{self.civitai_image_api_url}modelId={model_id}&modelVersionId={model_version_id}&postId={post_id}'
            r = self.httpx_client.get(url)
            image_info = r.json()['items']
            for image in image_info:
                if image['id'] == int(image_id):
                    return image['url']
        except Exception as e:
            print(e)
            raise

    def download_image(self, url: str):
        save_path = self.save_dir / Path(url.rsplit('/', 1)[-1])
        if save_path.exists():
            # todo: handle exists filename
            pass

        self.save_dir.mkdir(parents=True, exist_ok=True)

        try:
            r = self.httpx_client.get(url)
            r.raise_for_status()

            with open(save_path, 'wb') as f:
                for date in r.iter_bytes():
                    if date:
                        f.write(date)

            self.signals.download_completed_signal.emit(f'{url} download ok')
        except Exception as e:
            raise
