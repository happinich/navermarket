import json
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "daechi_1414_mobile_run.log"
REGISTRY_DIR = ROOT / "registry_docs"

K_WEB_OPEN = "웹브라우저에서 열기"
K_CONFIRM = "확인"
K_AD_SEND = "광고전송"
K_AD_SUBMIT = "광고하기"
K_VERIFY_SELECT = "검증방식 선택"
K_MOBILE2 = "모바일확인2"
K_PAYMENT = "1,900원 결제"
K_PRIVACY = "개인정보 수집 및 이용"
K_AGREE = "동의합니다"


def log(message: str) -> None:
    print(message, flush=True)


def save_state(page, stem: str) -> None:
    page.screenshot(path=str(ROOT / f"{stem}.png"), full_page=True)
    (ROOT / f"{stem}.html").write_text(page.content(), encoding="utf-8")


def click_first_visible(locator, label: str, timeout: int = 8000) -> bool:
    deadline = time.time() + timeout / 1000
    last_error = None
    while time.time() < deadline:
        count = locator.count()
        for i in range(count):
            item = locator.nth(i)
            try:
                if item.is_visible():
                    item.click(force=True, timeout=1500)
                    log(f"clicked: {label}")
                    return True
            except Exception as exc:
                last_error = exc
        time.sleep(0.3)
    log(f"could not click {label}: {last_error}")
    return False


def dispatch_input_events(locator) -> None:
    locator.evaluate(
        "el => { el.dispatchEvent(new Event('input', { bubbles: true })); "
        "el.dispatchEvent(new Event('change', { bubbles: true })); }"
    )


def open_gongsil(page, context, username: str, password: str) -> None:
    log("opening entry page")
    page.goto("https://www.gongsilclub.co.kr/", wait_until="load", timeout=30000)
    time.sleep(2)

    btn_open_web = page.locator(f"text={K_WEB_OPEN}")
    if btn_open_web.count() > 0:
        try:
            btn_open_web.first.click(timeout=10000)
            log("clicked web browser entry")
        except PlaywrightTimeoutError:
            btn_open_web.first.evaluate("el => el.click()")
            log("clicked web browser entry via js")
        time.sleep(5)
        if len(context.pages) > 1:
            page = context.pages[-1]
            page.wait_for_load_state("load", timeout=15000)
            log("web browser entry opened a new page")

    if page.locator("input[placeholder*='ID']").count() == 0:
        page.goto("https://www.gongsilclub.co.kr/group/login/", wait_until="load", timeout=30000)
        time.sleep(3)

    if page.locator("input[placeholder*='ID']").count() > 0:
        page.locator("input[placeholder*='ID']").first.fill(username)
        page.locator("input[type='password']").first.fill(password)
        page.locator("input[type='password']").first.press("Enter")
        log("login submitted")
        time.sleep(5)

    if page.get_by_text("다른 PC에서 로그인 중입니다").count() > 0:
        click_first_visible(page.get_by_text(K_CONFIRM, exact=True), "duplicate-login confirm")
        time.sleep(4)


def extract_verification_info(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    info = {
        "owner_name": "",
        "carrier": "",
        "phone": "",
        "gender": "",
        "relation": "본인",
    }

    owner_label = soup.find(string=lambda s: s and "등기부상의 소유자명" in s)
    if owner_label:
        label_cell = None
        curr = owner_label.parent
        for _ in range(8):
            classes = curr.get("class", []) if curr else []
            if curr and curr.name == "div" and any("background" in cls for cls in classes):
                label_cell = curr
                break
            curr = curr.parent if curr else None
        if label_cell:
            data_cell = label_cell.find_next_sibling()
            if data_cell:
                info["owner_name"] = data_cell.get_text(" ", strip=True).replace("*", "").strip()

    if not info["owner_name"]:
        for i, line in enumerate(lines):
            if "등기부상의 소유자명" in line:
                for candidate in lines[i + 1 : i + 8]:
                    if candidate not in {"*", ",", "개인", "법인"} and len(candidate) <= 12:
                        info["owner_name"] = candidate
                        break
                break

    phone_match = re.search(r"010-\d{3,4}-\d{4}", text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    for carrier in ["SKT알뜰폰", "KT알뜰폰", "LGU+알뜰폰", "SKT", "KT", "LGU+"]:
        if carrier in text:
            info["carrier"] = carrier
            break

    for gender in ["남", "여"]:
        if re.search(rf"\b{gender}\b", text):
            info["gender"] = gender
            break

    return info


def collect_old_verification(page) -> dict:
    log("opening management page for old listing")
    page.goto("https://www.gongsilclub.co.kr/group/management/", wait_until="load", timeout=30000)
    time.sleep(5)

    tab_btn = page.locator("text=종료·취소·실패").first
    tab_btn.wait_for(state="visible", timeout=10000)
    tab_btn.evaluate("el => el.click()")
    log("clicked: 종료·취소·실패 tab")
    time.sleep(5)
    save_state(page, "daechi_1414_stopped_list")

    old_card = page.locator("div.border-gray50").filter(has_text=re.compile("11583")).first
    old_card.wait_for(state="visible", timeout=15000)
    log("old card found:")
    log(old_card.inner_text())
    old_card.click(force=True)
    time.sleep(5)
    save_state(page, "daechi_1414_old_detail")

    info = extract_verification_info(page.content())
    log(f"collected old verification info: {info}")
    if not info["owner_name"] or not info["phone"]:
        raise RuntimeError(f"could not collect mobile verification info: {info}")
    return info


def choose_carrier(page, carrier: str) -> None:
    log(f"choosing carrier: {carrier}")
    dropdowns = [
        page.locator("xpath=//*[contains(text(), '통신사 선택')]/ancestor::div[contains(@style, 'cursor: pointer')][1]").first,
        page.locator("xpath=//*[contains(text(), '통신사')]/following::div[contains(@style, 'cursor: pointer')][1]").first,
    ]
    opened = False
    for dropdown in dropdowns:
        if dropdown.count() > 0:
            try:
                dropdown.click(force=True, timeout=3000)
                opened = True
                break
            except Exception:
                try:
                    dropdown.evaluate("el => el.click()")
                    opened = True
                    break
                except Exception:
                    pass
    if not opened:
        raise RuntimeError("carrier dropdown not found")
    time.sleep(1)
    if not click_first_visible(page.get_by_text(carrier, exact=True), f"carrier {carrier}", timeout=5000):
        raise RuntimeError(f"carrier option not found: {carrier}")


def fill_mobile_verification(page, info: dict) -> None:
    name_input = page.locator("input[name='verification.oname']").first
    name_input.wait_for(state="visible", timeout=10000)
    name_input.fill(info["owner_name"])
    dispatch_input_events(name_input)
    log(f"filled owner name: {info['owner_name']}")

    click_first_visible(page.locator("label").filter(has_text=re.compile("^개인$")), "개인", timeout=5000)

    if info.get("gender"):
        click_first_visible(page.locator("label").filter(has_text=re.compile(f"^{info['gender']}$")), f"gender {info['gender']}", timeout=5000)

    relation_dropdown = page.locator("xpath=//div[contains(., '의뢰인과 소유자와의 관계')]/following::div[contains(@style, 'cursor: pointer')][1]")
    if relation_dropdown.count() > 0:
        relation_dropdown.first.click(force=True)
        time.sleep(1)
        click_first_visible(page.get_by_text(info.get("relation", "본인"), exact=True), "relation 본인", timeout=5000)

    phone_parts = info["phone"].split("-")
    if len(phone_parts) != 3:
        raise RuntimeError(f"invalid phone format: {info['phone']}")
    prefix_dropdown = page.locator("xpath=//input[@name='dummyOphoneMiddle']/preceding::div[contains(@style, 'cursor: pointer')][1]").first
    if prefix_dropdown.count() > 0:
        prefix_dropdown.click(force=True)
        time.sleep(1)
        click_first_visible(page.get_by_text(phone_parts[0], exact=True), f"phone prefix {phone_parts[0]}", timeout=5000)
    middle = page.locator("input[name='dummyOphoneMiddle']").first
    tail = page.locator("input[name='dummyOphoneTail']").first
    middle.fill(phone_parts[1])
    tail.fill(phone_parts[2])
    dispatch_input_events(middle)
    dispatch_input_events(tail)
    log(f"filled phone: {info['phone']}")

    choose_carrier(page, info["carrier"] or "KT")
    save_state(page, "daechi_1414_mobile_filled")


def find_registry_pdf() -> Path:
    candidates = sorted(REGISTRY_DIR.glob("*.pdf"))
    preferred = [
        path for path in candidates
        if "1414" in path.name and ("등기" in path.name or "등기" in path.name)
    ]
    if preferred:
        return preferred[-1]
    if candidates:
        return candidates[-1]
    raise RuntimeError(f"registry PDF not found in {REGISTRY_DIR}")


def upload_registry_pdf(page) -> None:
    registry_pdf = find_registry_pdf()
    log(f"uploading registry PDF: {registry_pdf.name}")
    file_input = page.locator("input[type='file'][accept*='pdf']").last
    file_input.set_input_files(str(registry_pdf))
    time.sleep(4)
    save_state(page, "daechi_1414_registry_uploaded")


def select_registry_from_history(page) -> bool:
    history_button = page.get_by_text("열람 내역", exact=True)
    if history_button.count() == 0:
        return False
    click_first_visible(history_button, "열람 내역", timeout=5000)
    time.sleep(4)
    save_state(page, "daechi_1414_registry_history")

    candidates = [
        page.get_by_text("대치3차1414호_등기부.pdf", exact=True),
        page.locator("text=대치3차"),
        page.locator("text=1414"),
    ]
    for candidate in candidates:
        if click_first_visible(candidate, "registry history candidate", timeout=3000):
            time.sleep(2)
            save_state(page, "daechi_1414_registry_history_selected")
            return True
    return False


def agree_terms_and_pay(page) -> None:
    click_first_visible(page.get_by_text("Gpay", exact=False), "Gpay option", timeout=3000)
    if page.get_by_text("새로고침", exact=True).count() > 0:
        click_first_visible(page.get_by_text("새로고침", exact=True), "Gpay 새로고침", timeout=3000)
        time.sleep(1)

    terms_card = page.locator(
        "xpath=//*[contains(text(), '개인정보 수집 및 이용')]/ancestor::div[contains(@style, 'cursor: pointer')][1]"
    )
    terms_card.first.scroll_into_view_if_needed(timeout=5000)
    box = terms_card.first.bounding_box()
    if not box:
        raise RuntimeError("terms card has no bounding box")
    page.mouse.click(box["x"] + 27, box["y"] + 31)
    log("opened 개인정보 동의 popup")
    time.sleep(2)

    if page.get_by_text(K_AGREE, exact=True).count() > 0:
        agree_label = page.get_by_text(K_AGREE, exact=True).last
        agree_label.wait_for(state="visible", timeout=5000)
        label_box = agree_label.bounding_box()
        if not label_box:
            raise RuntimeError("약관 동의 checkbox has no bounding box")
        page.mouse.click(label_box["x"] - 24, label_box["y"] + label_box["height"] / 2)
        log("clicked: 약관 동의")
        time.sleep(3)

    save_state(page, "daechi_1414_before_final_payment")
    page.wait_for_function(
        """() => [...document.querySelectorAll('div.button')]
            .some(el => el.textContent.includes('1,900원 결제') && !el.className.includes('disabled'))""",
        timeout=10000,
    )
    pay_button = page.locator("div.button").filter(has_text=re.compile(K_PAYMENT)).first
    pay_button.click(force=True, timeout=5000)
    log("clicked final 1,900원 결제")
    time.sleep(10)
    save_state(page, "daechi_1414_ad_complete")


def main() -> None:
    sys.stdout = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    username = config["gongsilclub"]["username"]
    password = config["gongsilclub"]["password"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("dialog", lambda dialog: (log(f"dialog: {dialog.message}"), dialog.accept()))

        open_gongsil(page, context, username, password)
        page = context.pages[-1]

        info = collect_old_verification(page)

        log("opening management page for new listing")
        page.goto("https://www.gongsilclub.co.kr/group/management/", wait_until="load", timeout=30000)
        time.sleep(5)
        save_state(page, "daechi_1414_management_before")

        card = page.locator("div.border-gray50").filter(has_text=re.compile("13169")).first
        card.wait_for(state="visible", timeout=15000)
        card_text = card.inner_text()
        log("target card found:")
        log(card_text)

        if "광고중" in card_text or "검증대기" in card_text or "네이버 부동산" in card_text:
            save_state(page, "daechi_1414_already_sent")
            log("target already appears to be sent; stopping")
            browser.close()
            return

        if not click_first_visible(card.get_by_text(K_AD_SEND, exact=True), "광고전송"):
            raise RuntimeError("광고전송 button not found on target card")
        time.sleep(3)

        if page.get_by_text(K_AD_SUBMIT, exact=True).count() > 0:
            click_first_visible(page.get_by_text(K_AD_SUBMIT, exact=True), "광고하기")
            time.sleep(6)

        page.get_by_text(K_VERIFY_SELECT).first.wait_for(state="visible", timeout=20000)
        save_state(page, "daechi_1414_verify_choices")

        mobile2_card = page.locator("form div.border-gray50").filter(has_text=re.compile(K_MOBILE2)).last
        mobile2_card.wait_for(state="visible", timeout=10000)
        mobile2_card.click(force=True)
        log("selected 모바일확인2")
        time.sleep(5)

        fill_mobile_verification(page, info)
        upload_registry_pdf(page)
        agree_terms_and_pay(page)

        browser.close()


if __name__ == "__main__":
    main()
