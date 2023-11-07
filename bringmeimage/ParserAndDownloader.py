from pathlib import Path
import re

import httpx
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from bringmeimage.BringMeImageData import ImageData, VersionIdData


class ImageUrlParserSignal(QObject):
    ImageUrlParser_Processed_Signal = Signal()
    ImageUrlParser_Completed_Signal = Signal(tuple)


class ImageUrlParserRunner(QRunnable):
    def __init__(self, legal_url_dict: dict):
        super().__init__()
        self.legal_url_dict = legal_url_dict
        self.legal_url_parse_completed_dict = {}
        self.legal_url_parse_failed_dict = {}
        self.re_parser = re.compile(r'/models/(?P<modelId>\d+)/.*modelVersionId=(?P<modelVersionId>\d+)')
        self.images_info = []
        self.signals = ImageUrlParserSignal()

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        self.webdriver = webdriver.Firefox(options=options)

    @Slot()
    def run(self) -> None:
        self.get_image_info()

    def get_image_info(self):
        script = """
        let imgElement = document.querySelector('.mantine-1ynvwjz img');
        let aElement = document.querySelector('.mantine-1snf94l a');
        if (imgElement && aElement) {
            var imgSrc = imgElement.getAttribute('src');
            var aHref = aElement.getAttribute('href');
            return [imgSrc, aHref];
        } else {
            return null;
        }
        """
        for image_url in self.legal_url_dict:
            if self.legal_url_dict[image_url].is_parsed:
                self.legal_url_parse_completed_dict[image_url] = self.legal_url_dict[image_url]
                self.signals.ImageUrlParser_Processed_Signal.emit()
                continue

            try:
                self.webdriver.get(image_url)
                wait = WebDriverWait(self.webdriver, 10)
                if result := wait.until(lambda driver: self.webdriver.execute_script(script)):
                    real_url, model_version_href = result
                    match = self.re_parser.match(model_version_href)
                    image_data = self.legal_url_dict[image_url]
                    image_data.real_url = real_url
                    image_data.modelVersionId = match.group('modelVersionId')
                    image_data.is_parsed = True
                    self.legal_url_parse_completed_dict[image_url] = image_data
                else:
                    self.legal_url_parse_failed_dict[image_url] = self.legal_url_dict[image_url]
            except TimeoutException as e:
                self.legal_url_parse_failed_dict[image_url] = self.legal_url_dict[image_url]
            finally:
                self.signals.ImageUrlParser_Processed_Signal.emit()

        self.webdriver.quit()
        self.signals.ImageUrlParser_Completed_Signal.emit(
            (self.legal_url_parse_completed_dict, self.legal_url_parse_failed_dict)
        )


class VersionIdParserRunnerSignals(QObject):
    VersionIdParser_Failed_Signal = Signal()
    VersionIdParser_Completed_Signal = Signal(dict)


class VersionIdParserRunner(QRunnable):
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

        self.signals = VersionIdParserRunnerSignals()

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

            version_id_info = {self.version_id: VersionIdData(version_name, model_id, model_name, creator)}
            self.signals.VersionIdParser_Completed_Signal.emit(version_id_info)
        except Exception as e:
            self.signals.VersionIdParser_Failed_Signal.emit()


class DownloadRunnerSignals(QObject):
    download_failed_signal = Signal(ImageData)
    download_completed_signal = Signal()


class DownloadRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, image_data: ImageData, save_dir: Path,
                 categorize: bool, version_id_info_dict: dict):
        super().__init__()
        self.httpx_client = httpx_client

        self.image_data = image_data
        self.save_dir = save_dir
        self.categorize = categorize
        self.version_id_info_dict = version_id_info_dict
        self.model_name = ''
        self.version_name = ''

        self.signals = DownloadRunnerSignals()

    @Slot()
    def run(self) -> None:
        self.save_dir = self.get_save_path()
        self.download_image()

    def get_save_path(self) -> Path:
        if not self.categorize:
            return self.save_dir

        # Have to handle the model name like 'Skirt tug / dress tug / clothes tug'
        # hint: version_id_info_dict = {version_id: dataclass(version_name, model_id, model_name, creator), ...}
        modelVersionId = self.image_data.modelVersionId
        self.model_name = self.version_id_info_dict[modelVersionId].model_name.replace('/', '_').replace('\\', '_')
        self.version_name = self.version_id_info_dict[modelVersionId].version_name.replace('/', '_').replace('\\', '_')
        return self.save_dir / self.model_name / self.version_name / 'gallery'

    def download_image(self) -> None:
        self.save_dir.mkdir(parents=True, exist_ok=True)
        real_url = self.image_data.real_url
        save_path = self.save_dir / Path(real_url.rsplit('/', 1)[-1])
        if save_path.exists():
            new_name = f'{save_path.stem}(repeat){save_path.suffix}'
            save_path = save_path.with_name(new_name)

        try:
            r = self.httpx_client.get(real_url)
            r.raise_for_status()

            with open(save_path, 'wb') as f:
                for date in r.iter_bytes():
                    if date:
                        f.write(date)

            self.signals.download_completed_signal.emit()
        except Exception as e:
            self.signals.download_failed_signal.emit(self.image_data)


if __name__ == '__main__':
    test_image_dict = {'https://civitai.com/images/2940879': ImageData(url='https://civitai.com/images/2940879', imageId='2940879'),
                       'https://civitai.com/images/3222147': ImageData(url='https://civitai.com/images/3222147', imageId='3222147'),
                       }
    runner = ImageUrlParserRunner(legal_url_dict=test_image_dict)
    runner.run()
