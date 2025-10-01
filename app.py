import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from flask import Flask, request

# Lokasi ekstensi relatif (pastikan file ada di repo)
EXT_PATH = "./extension.crx"

# Setup Chrome + Extension
options = webdriver.ChromeOptions()
options.add_extension(EXT_PATH)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless")  # hapus kalau mau lihat UI asli

# Path chromedriver biarkan default, asumsikan sudah ada di PATH
driver = webdriver.Chrome(service=Service("chromedriver"), options=options)

# Tunggu load
time.sleep(5)

# Flask untuk UI login mirip ekstensi
app = Flask(__name__)

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Node Login</title>
</head>
<body style="font-family: sans-serif; background: #fafafa; text-align:center;">
    <h2>Login HedNet Node</h2>
    <form method="post" action="/login">
        <input type="text" name="username" placeholder="Username" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML_UI

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        # Load halaman utama ekstensi (ganti sesuai path file HTML di ekstensi)
        driver.get("chrome-extension://jgmekddkhffanioefjcgfaggjpokifpi/index.html")
        time.sleep(3)

        # Ganti selector sesuai UI ekstensi
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()

        return f"Login sukses untuk {username}"
    except Exception as e:
        return f"Gagal login: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
