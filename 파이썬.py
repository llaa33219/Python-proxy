import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QToolBar, QAction
from PyQt5.QtCore import QUrl, QByteArray
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineUrlScheme,
    QWebEngineUrlRequestJob,
    QWebEngineUrlSchemeHandler
)
import requests
from urllib.parse import urlparse

# 커스텀 스킴 등록 (proxy://)
custom_scheme = QWebEngineUrlScheme(b"proxy")
# SecureScheme: 보안 스킴 처럼 동작 (https 처럼)
# LocalScheme: 로컬 리소스처럼 취급
# LocalAccessAllowed: 로컬 접근 허용
# 필요에 따라 플래그 조정 가능
custom_scheme.setFlags(QWebEngineUrlScheme.SecureScheme | QWebEngineUrlScheme.LocalScheme | QWebEngineUrlScheme.LocalAccessAllowed)
QWebEngineUrlScheme.registerScheme(custom_scheme)

class ProxySchemeHandler(QWebEngineUrlSchemeHandler):
    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl()
        host = url.host()
        path = url.path()

        # 실제 인터넷 요청 시도
        # HTTPS -> HTTP 순서로 시도
        full_url = f"https://{host}{path}"
        try:
            resp = requests.get(full_url, verify=False)
        except:
            full_url = f"http://{host}{path}"
            resp = requests.get(full_url)

        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', 'text/html')
            data = resp.content
            job.reply(content_type.encode('utf-8'), QByteArray(data))
        else:
            # 오류 페이지
            error_html = f"<html><body><h1>Error {resp.status_code}</h1></body></html>"
            job.reply(b"text/html", QByteArray(error_html.encode('utf-8')))

class Browser(QMainWindow):
    def __init__(self, start_url):
        super().__init__()
        self.setWindowTitle("Python Proxy Browser")

        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        profile = QWebEngineProfile.defaultProfile()
        self.handler = ProxySchemeHandler(profile)
        profile.installUrlSchemeHandler(b"proxy", self.handler)

        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_from_url_bar)
        toolbar.addWidget(self.url_bar)

        back_action = QAction("←", self)
        back_action.triggered.connect(self.view.back)
        toolbar.addAction(back_action)

        forward_action = QAction("→", self)
        forward_action.triggered.connect(self.view.forward)
        toolbar.addAction(forward_action)

        reload_action = QAction("⟳", self)
        reload_action.triggered.connect(self.view.reload)
        toolbar.addAction(reload_action)

        self.load_url(start_url)

    def load_url(self, input_url):
        parsed = urlparse(input_url)
        host = parsed.netloc if parsed.netloc else parsed.path
        path = parsed.path if parsed.path else '/'
        proxy_url = QUrl(f"proxy://{host}{path}")
        self.view.load(proxy_url)
        self.url_bar.setText(input_url)

    def load_from_url_bar(self):
        url_text = self.url_bar.text().strip()
        if not url_text.startswith("http"):
            url_text = "https://" + url_text
        self.load_url(url_text)

if __name__ == "__main__":
    start_url = input("접속할 사이트 URL을 입력하세요 (예: https://www.example.com): ").strip()
    if not start_url:
        start_url = "https://www.example.com"

    app = QApplication(sys.argv)
    browser = Browser(start_url)
    browser.resize(1200, 800)
    browser.show()
    sys.exit(app.exec_())
