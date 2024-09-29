import pickle
from pathlib import Path

from selenium.webdriver.chrome.webdriver import WebDriver

from bringmeimage.LoggerConf import get_logger
Logger = get_logger(__name__)


class LoadCookieError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class LoginCivitAi:
    Web_Driver_Load_Timeout: int = 5
    Check_Url: str = r'https://civitai.com/models/10364/innies-better-vulva'
    Check_Title: str = r'Innies: Better vulva - v1.1 | Stable Diffusion LoRA | Civitai'

    def __init__(self, driver: WebDriver, cookie_file: Path) -> None:
        self.driver = driver
        self.cookie_file = cookie_file

    def auto_login(self) -> bool:
        try:
            self.driver.set_page_load_timeout(self.Web_Driver_Load_Timeout)
            self.driver.get('https://civitai.com/')
            self.load_cookie()
            self.is_login_successful()
            return True
        except Exception as e:
            Logger.exception(e)

        self.driver.quit()
        return False

    def load_cookie(self) -> None:
        with self.cookie_file.open('rb') as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            if cookie['name'] == '__Host-next-auth.csrf-token':
                continue
            self.driver.add_cookie(cookie)

    def is_login_successful(self) -> None:
        self.driver.refresh()
        self.driver.get(self.Check_Url)

        if self.driver.title != self.Check_Title:
            raise LoadCookieError('Check failed')

        cookies: list[dict] = self.driver.get_cookies()
        with self.cookie_file.open('wb') as f:
            pickle.dump(cookies, f)
