import contextlib
from pathlib import Path

import httpx
from PySide6.QtCore import QObject, Signal, QRunnable, Slot


class ParserRunnerSignals(QObject):
    Parser_connect_to_api_failed_signal = Signal(tuple)
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
            r = self.httpx_client.get(self.civitai_model_api_url + model_id)
            self.signals.Parser_completed_signal.emit((True, {model_id: r.json()["name"]}, 'Preprocessing'))
        except Exception as e:
            self.signals.Parser_connect_to_api_failed_signal.emit((f'model:{model_id}, {e}', 'Preprocessing'))

    def get_version_name(self, version_id: str) -> None:
        try:
            r = self.httpx_client.get(self.civitai_version_api_url + version_id)
            self.signals.Parser_completed_signal.emit((False, {version_id: r.json()["name"]}, 'Preprocessing'))
        except Exception as e:
            self.signals.Parser_connect_to_api_failed_signal.emit((f'version:{version_id}, {e}', 'Preprocessing'))


class DownloadRunnerSignals(QObject):
    download_connect_to_api_failed_signal = Signal(tuple)
    download_completed_signal = Signal(tuple)


class DownloadRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, image_info: tuple, save_dir: Path,
                 categorize:bool, model_and_version_name: tuple):
        super().__init__()
        self.httpx_client = httpx_client
        self.image_original_url, self.image_params = image_info
        # self.image_params = (model_id, model_version_id, post_id, image_id)
        self.save_dir = save_dir
        self.categorize = categorize
        self.model_name_dict, self.version_name_dict = model_and_version_name or ({}, {})

        self.civitai_image_api_url = 'https://civitai.com/api/v1/images?'
        self.signals = DownloadRunnerSignals()

    @Slot()
    def run(self) -> None:
        self.save_dir = self.get_save_path()
        url = self.get_real_image_url() if self.image_params else self.image_original_url
        self.download_image(url)

    def get_save_path(self) -> Path:
        if not self.image_params or not self.categorize:
            return self.save_dir

        # Have to handle the model name like 'Skirt tug / dress tug / clothes tug'
        model_name: str = self.model_name_dict[self.image_params[0]].replace('/', '_').replace('\\', '_')
        version_name: str = self.version_name_dict[self.image_params[1]].replace('/', '_').replace('\\', '_')
        return self.save_dir / model_name / version_name / 'gallery'

    def get_real_image_url(self) -> str:
        model_id, model_version_id, post_id, image_id = self.image_params

        with contextlib.suppress(Exception):
            url = f'{self.civitai_image_api_url}modelId={model_id}&modelVersionId={model_version_id}&postId={post_id}'
            r = self.httpx_client.get(url)
            image_info = r.json()['items']
            if real_url := next(
                (
                    image['url']
                    for image in image_info
                    if image['id'] == int(image_id)
                ),
                '',
            ):
                return real_url

        self.signals.download_connect_to_api_failed_signal.emit(
            (self.image_original_url,
             self.model_name_dict.get(self.image_params[0]),
             self.version_name_dict.get(self.image_params[1]),
             'Fail to get a real url',
             'Downloading')
        )
        return ''

    def download_image(self, url: str):
        if not url:
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
        except Exception as _:
            self.signals.download_connect_to_api_failed_signal.emit(
                (self.image_original_url,
                 self.model_name_dict.get(self.image_params[0]),
                 self.version_name_dict.get(self.image_params[1]),
                 'Download failed',
                 'Downloading')
            )
