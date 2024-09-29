from pathlib import Path

import httpx
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

from bringmeimage.BringMeImageData import ImageData
from bringmeimage.LoggerConf import get_logger
logger = get_logger(__name__)


class DownloadRunnerSignals(QObject):
    download_failed_signal = Signal(ImageData)
    download_completed_signal = Signal()


class DownloadRunner(QRunnable):
    def __init__(self, httpx_client: httpx.Client, image_data: ImageData, save_dir: Path):
        super().__init__()
        self.httpx_client = httpx_client
        self.signals = DownloadRunnerSignals()
        self.image_data = image_data
        self.save_dir = save_dir

    @Slot()
    def run(self) -> None:
        self.download()

    def download(self) -> None:
        self.save_dir.mkdir(parents=True, exist_ok=True)
        src = self.image_data.src
        full_img_name = src.rsplit('/', maxsplit=1)[-1]
        img_name, extension = full_img_name.rsplit('.', maxsplit=1)
        img_name = img_name[:20] if len(img_name) > 20 else img_name
        save_path = self.save_dir / f'{img_name}.{extension}'
        if save_path.exists():
            new_name = f'{save_path.stem}(repeat){save_path.suffix}'
            save_path = save_path.with_name(new_name)

        try:
            r = self.httpx_client.get(src)
            r.raise_for_status()

            with open(save_path, 'wb') as f:
                for date in r.iter_bytes():
                    if date:
                        f.write(date)

            self.signals.download_completed_signal.emit()
        except Exception as e:
            self.signals.download_failed_signal.emit(self.image_data)
            logger.info(f'Download exception{e}: Image src: {src}')
